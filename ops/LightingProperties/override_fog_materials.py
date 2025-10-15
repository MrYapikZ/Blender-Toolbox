import bpy


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
