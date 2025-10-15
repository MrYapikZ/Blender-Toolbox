import bpy


# ------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------
def ensure_obj_and_data_override(obj):
    """Make a library override for the object (and its data) so we can edit materials."""
    data = getattr(obj, "data", None)
    needs = (not getattr(obj, "override_library", None)) or (
            data and data.library and not getattr(data, "override_library", None)
    )
    if not needs:
        return obj

    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    try:
        bpy.ops.object.make_override_library(hierarchy=True)  # Blender 3.x/4.x
    except TypeError:
        bpy.ops.object.make_override_library()  # fallback for very old versions

    return bpy.context.view_layer.objects.active


def localize_linked_node_groups(material):
    """Make linked node groups inside the material local so they’re editable."""
    if not material.use_nodes or not material.node_tree:
        return
    for node in material.node_tree.nodes:
        if node.type == 'GROUP' and node.node_tree and node.node_tree.library:
            node.node_tree = node.node_tree.copy()  # becomes local


def override_materials_for_object(obj, localize_groups=True, verbose=True):
    """Localize linked materials on obj.data.materials and reassign them."""
    data = getattr(obj, "data", None)
    mats = getattr(data, "materials", None) if data else None
    if not mats:
        if verbose:
            print(f"'{obj.name}' has no material slots.")
        return 0

    changed = 0
    for i, mat in enumerate(list(mats)):
        if mat is None:
            continue

        # Already editable?
        if (mat.library is None) or getattr(mat, "override_library", None):
            if localize_groups:
                localize_linked_node_groups(mat)
            if verbose:
                print(f"[{obj.name}] Slot {i}: '{mat.name}' already editable.")
            continue

        # Replace with local copy (no manual renaming)
        local_mat = mat.copy()  # local; name may auto-unique if clash
        mats[i] = local_mat
        if localize_groups:
            localize_linked_node_groups(local_mat)
        changed += 1
        if verbose:
            print(f"[{obj.name}] Slot {i}: linked '{mat.name}' → local '{local_mat.name}'")
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
        obj = bpy.data.objects.get(self.object_name)
        if not obj:
            self.report({'ERROR'}, f"No object named '{self.object_name}' found.")
            return {'CANCELLED'}

        # Step 1: ensure library override (object + data)
        obj_ovr = ensure_obj_and_data_override(obj)

        # Step 2: localize linked materials (no renaming)
        changed = override_materials_for_object(obj_ovr, self.localize_groups, verbose=True)

        self.report({'INFO'}, f"'{obj_ovr.name}' materials editable. Localized {changed} linked material(s).")
        return {'FINISHED'}


# ------------------------------------------------------------------------
# Register
# ------------------------------------------------------------------------
def register():
    bpy.utils.register_class(BLP_OT_override_fog_materials)


def unregister():
    bpy.utils.unregister_class(BLP_OT_override_fog_materials)
