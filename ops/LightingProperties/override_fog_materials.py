import bpy
from collections import deque


# ------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------
def find_instanced_collections_with_object(target_name: str):
    """Yield (instancer_empty, instanced_collection) where collection contains target object by name."""
    for obj in bpy.data.objects:
        if obj.type == 'EMPTY' and getattr(obj, "instance_type", None) == 'COLLECTION':
            coll = getattr(obj, "instance_collection", None)
            if not coll:
                continue
            # coll.all_objects includes nested children if available
            objs = getattr(coll, "all_objects", coll.objects)
            for o in objs:
                if o and (o.name == target_name or o.name.split(".", 1)[0] == target_name):
                    yield (obj, coll)
                    break


def make_override_from_instancer(instancer_obj):
    """
    Select the collection-instancer empty and run Make Library Override.
    Blender 4.5 removed the 'hierarchy' keyword; the operator decides scope internally.
    """
    bpy.ops.object.select_all(action='DESELECT')
    instancer_obj.select_set(True)
    bpy.context.view_layer.objects.active = instancer_obj

    # 4.5+: no keyword; older: also fine without kwargs.
    bpy.ops.object.make_override_library()
    return True


def localize_linked_node_groups(material):
    """If material uses linked node groups, copy them to local so edits stick."""
    if not material or not material.use_nodes or not material.node_tree:
        return
    for node in material.node_tree.nodes:
        if node.type == 'GROUP' and node.node_tree and node.node_tree.library:
            node.node_tree = node.node_tree.copy()


def localize_materials_on_object(obj, localize_groups=True):
    """Replace linked materials on obj.data.materials with local copies. Returns count."""
    data = getattr(obj, "data", None)
    mats = getattr(data, "materials", None) if data else None
    if not mats:
        return 0
    changed = 0
    for i, mat in enumerate(list(mats)):
        if mat is None:
            continue
        # Already local/overridden? Keep; optionally localize inner node groups.
        if (mat.library is None) or getattr(mat, "override_library", None):
            if localize_groups:
                localize_linked_node_groups(mat)
            continue
        # Make local copy (name may auto-unique if a clash exists).
        local_mat = mat.copy()
        mats[i] = local_mat
        if localize_groups:
            localize_linked_node_groups(local_mat)
        changed += 1
    return changed


def is_override(idblock):
    return getattr(idblock, "override_library", None) is not None


def is_linked(idblock):
    return getattr(idblock, "library", None) is not None


def find_override_for_reference(idblock):
    """Return the override that points to 'idblock' as its reference, if any."""
    if idblock is None:
        return None

    pools = []
    if isinstance(idblock, bpy.types.Collection):
        pools.append(bpy.data.collections)
    elif isinstance(idblock, bpy.types.Object):
        pools.append(bpy.data.objects)
    else:
        pools = [bpy.data.collections, bpy.data.objects]

    for pool in pools:
        for candidate in pool:
            ol = getattr(candidate, "override_library", None)
            if ol and ol.reference == idblock:
                return candidate
    return None


def ensure_collection_override_hierarchy(col, scene, view_layer):
    """Create or fetch an override for a collection as a hierarchy root."""
    if col is None:
        return None
    if is_override(col):
        return col
    if not is_linked(col):
        return col

    ov = find_override_for_reference(col)
    if ov:
        return ov

    ov = col.override_hierarchy_create(scene=scene, view_layer=view_layer)
    return ov


def iter_collections_recursive(col):
    """Yield collections depth-first, including children."""
    yield col
    for c in col.children:
        yield from iter_collections_recursive(c)


def iter_objects_recursive(col):
    """Yield all objects contained (recursively) in a collection hierarchy."""
    for obj in col.objects:
        yield obj
    for child in col.children:
        yield from iter_objects_recursive(child)


def ensure_instance_collection_overrides(root_override, scene, view_layer):
    """
    Follow object->instance_collection links and ensure those collections are overridden too.
    """
    if not root_override:
        return

    queue = deque([root_override])
    seen = set()
    while queue:
        col = queue.popleft()
        if col in seen:
            continue
        seen.add(col)

        # Remap instanced collections to their overrides
        for obj in col.objects:
            if getattr(obj, "instance_type", None) == 'COLLECTION' and obj.instance_collection:
                inst_col = obj.instance_collection
                if is_linked(inst_col) or find_override_for_reference(inst_col):
                    ov_inst = ensure_collection_override_hierarchy(inst_col, scene, view_layer)
                    if ov_inst and obj.instance_collection != ov_inst:
                        try:
                            obj.instance_collection = ov_inst
                        except Exception:
                            pass
                    if ov_inst:
                        queue.append(ov_inst)

        for child in col.children:
            queue.append(child)


def make_meshes_local_in_hierarchy(root_col):
    """Make mesh datablocks local for all mesh objects under root_col."""
    if not root_col:
        return
    for obj in iter_objects_recursive(root_col):
        if obj.type == 'MESH' and obj.data and is_linked(obj.data):
            obj.data = obj.data.copy()


def _find_holder(root, child):
    """Return the direct parent collection of 'child' under 'root' (DFS)."""
    for c in root.children:
        if c == child:
            return root
        h = _find_holder(c, child)
        if h:
            return h
    return None


def _path_to_collection(root_col, target):
    """Return the ancestry path [root_col ... target] or [] if not found."""
    if root_col == target:
        return [root_col]
    for c in root_col.children:
        path = _path_to_collection(c, target)
        if path:
            return [root_col] + path
    return []


# ========================================
# Locating root collection by object name
# (adapted from your helper, minimal edits)
# ========================================

def get_collections_containing_object_in_scene(obj_name, scene=None):
    """Return all collections (under scene root) that directly contain the object."""
    obj = bpy.data.objects.get(obj_name)
    if not obj:
        print(f"No object named '{obj_name}' found.")
        return []

    if scene is None:
        scene = bpy.context.scene

    collections = []

    def _search(col):
        if obj.name in col.objects:
            collections.append(col)
        for child in col.children:
            _search(child)

    _search(scene.collection)
    return collections


def pick_rootmost_linked_collection(candidates, scene_root):
    """
    From a set of collections that contain the object, pick the highest (closest to scene root)
    *linked* ancestor that actually contains that candidate in its subtree.
    If none are linked, fall back to the highest local/overridden ancestor.
    """
    if not candidates:
        return None

    # For each candidate, compute its path to the scene root
    paths = []
    for col in candidates:
        path = _path_to_collection(scene_root, col)
        if path:
            paths.append(path)

    # Sort by path length ascending => shortest path means higher up in hierarchy
    paths.sort(key=len)
    if not paths:
        # Could be in view layers or other holders, fallback to just return first candidate
        return candidates[0]

    # Try to find the highest ancestor in each path that is linked; prefer linked
    for path in paths:
        # path like [scene_root, ..., parent, candidate]
        # Walk from scene_root downward, pick the highest linked ancestor that still contains the candidate
        linked_ancestors = [c for c in path if is_linked(c)]
        if linked_ancestors:
            return linked_ancestors[0]

    # If nothing linked on any path, return the highest ancestor (rootmost) anyway
    return paths[0][0] if len(paths[0]) > 1 else paths[0][-1]


# ------------------------------------------------------------------------
# Operator: Override 'Fog' Materials
# ------------------------------------------------------------------------
class BLP_OT_override_fog_materials(bpy.types.Operator):
    """Override a linked object and localize its materials so they’re editable (no renaming)."""
    bl_idname = "blp.override_fog_materials"
    bl_label = "Override Fog Materials"
    bl_options = {'REGISTER', 'UNDO'}

    object_name: bpy.props.StringProperty(
        name="Object Name",
        description="Target object to override and localize materials for",
        default="Fog",
    )
    localize_groups: bpy.props.BoolProperty(
        name="Localize Node Groups",
        description="Also duplicate linked node-groups used by the materials",
        default=True,
    )

    def execute(self, context):
        target = self.object_name
        scene = bpy.context.scene
        view_layer = bpy.context.view_layer
        MAKE_GEOMETRY_LOCAL = True  # your original toggle

        # 1) Locate collections that contain the target object under the *scene* tree
        cand_cols = get_collections_containing_object_in_scene(target, scene=scene)

        if not cand_cols:
            raise RuntimeError(f"No collections under the scene contain object '{target}'.")

        # 2) Choose the root-most (near scene root) *linked* collection to treat as the hierarchy root.
        root_col = pick_rootmost_linked_collection(cand_cols, scene.collection)
        if not root_col:
            # As a fallback, try the first candidate
            root_col = cand_cols[0]

        print(f"Selected hierarchy root collection: '{root_col.name}'")

        # 3) Ensure override for that root
        print(f"Ensuring override hierarchy for '{root_col.name}'...")
        root_override = ensure_collection_override_hierarchy(root_col, scene, view_layer)

        # 4) Follow child + instanced collections to ensure overrides exist
        print("Following hierarchy (children + instanced collections) and ensuring overrides...")
        ensure_instance_collection_overrides(root_override, scene, view_layer)

        # 5) Optional: make geometries local while keeping objects/collections overridden
        if MAKE_GEOMETRY_LOCAL:
            print("Making mesh data local for all Mesh objects under the overridden hierarchy...")
            make_meshes_local_in_hierarchy(root_override)

        # 6) Unlink the linked original holder to avoid duplicates in the scene tree
        #    (kept your original pattern, fixed minor variable typo)
        holder = _find_holder(scene.collection, root_col)
        if holder:
            try:
                holder.children.unlink(root_col)
                print(f"Unlinked linked original '{root_col.name}' from '{holder.name}'")
            except RuntimeError as e:
                # Fallback: try scene root if the holder is itself linked or context-bound
                try:
                    if root_col.name in scene.collection.children.keys():
                        scene.collection.children.unlink(root_col)
                        print(f"Forced unlink at scene root for '{root_col.name}'")
                    else:
                        print(f"Could not unlink linked original '{root_col.name}': {e}")
                except Exception as e2:
                    print(f"Second-chance unlink failed for '{root_col.name}': {e2}")
        else:
            print(f"Linked original '{root_col.name}' not found under scene; nothing to unlink")

        print(f"Done. Root override: '{root_override.name if root_override else 'None'}'")

        # ===============================
        # (Optional) Per-object override
        # If you still want: make the target mesh data local directly by name.
        # ===============================
        obj = bpy.data.objects.get(target)
        if obj and obj.type == 'MESH' and obj.data and is_linked(obj.data):
            try:
                obj.data = obj.data.copy()
                print(f"Made mesh data local for '{obj.name}'.")
            except Exception as e:
                print(f"Could not localize mesh data for '{obj.name}': {e}")

        # If Fog already exists (e.g., already overridden), skip the collection search.
        fog = bpy.data.objects.get(target)
        if not fog:
            candidates = list(find_instanced_collections_with_object(target))
            if not candidates:
                self.report({'ERROR'}, f"No collection instance in the scene appears to contain '{target}'.")
                return {'CANCELLED'}

            instancer_obj, _ = candidates[0]
            try:
                make_override_from_instancer(instancer_obj)
            except RuntimeError as e:
                self.report({'ERROR'}, f"Make Override failed: {e}")
                return {'CANCELLED'}

            # Try to fetch Fog again (exact or base-name match)
            fog = bpy.data.objects.get(target)
            if not fog:
                fog = next((o for o in bpy.data.objects
                            if o.name == target or o.name.split(".", 1)[0] == target), None)
                if not fog:
                    self.report({'ERROR'}, f"After overriding, '{target}' was not found.")
                    return {'CANCELLED'}

        # Localize Fog's materials (no renaming)
        changed = localize_materials_on_object(fog, self.localize_groups)
        self.report({'INFO'}, f"Parent collection overridden. Localized {changed} material(s) on '{fog.name}'.")
        return {'FINISHED'}


# ------------------------------------------------------------------------
# Register
# ------------------------------------------------------------------------
def register():
    bpy.utils.register_class(BLP_OT_override_fog_materials)


def unregister():
    bpy.utils.unregister_class(BLP_OT_override_fog_materials)
