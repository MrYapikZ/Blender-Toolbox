import bpy
from ...utils.file_manager import FileManager


# ------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------
def ensure_root_child(parent_coll: bpy.types.Collection, child_coll: bpy.types.Collection):
    """Link child_coll under parent_coll if not already linked anywhere; if already has a parent, don't duplicate."""
    # If it already lives under parent_coll, do nothing
    if child_coll.name in parent_coll.children.keys():
        return
    # Collections can have multiple parents in Blender; safe to link.
    parent_coll.children.link(child_coll)


def unique_collection_name(base: str) -> str:
    """Return a name that's not used by any existing collection."""
    if bpy.data.collections.get(base) is None:
        return base
    i = 0o01
    while True:
        cand = f"{base}.{i:03d}"
        if bpy.data.collections.get(cand) is None:
            return cand
        i += 1


# ------------------------------------------------------------------------
# Lighting Setup - Append Blend File
# ------------------------------------------------------------------------
class LIGHTINGSETUP_OT_AppendBlend(bpy.types.Operator):
    bl_idname = "bls.append_blend"
    bl_label = "Append Lighting Setup"
    bl_description = "Append lighting setup from presets blend file"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        s = context.scene
        props = s.lighting_setup
        raw_path = props.filepath
        filepath = FileManager.get_filepath(raw_path)
        if not filepath:
            self.report({'ERROR'}, "No presets file path specified")
            return {'CANCELLED'}

        # Detect selected collection
        layer_coll = getattr(context.view_layer, "active_layer_collection", None)
        if not layer_coll:
            self.report({'ERROR'}, "No active collection. Click a collection in the Outliner first.")
            return {'CANCELLED'}

        active_coll = layer_coll.collection
        sel_name = active_coll.name

        # Check if collection name starts with 'c-'
        if sel_name.lower().startswith("c-"):
            suffix = sel_name[2:] or sel_name  # handle 'c-' edge-case
        else:
            self.report({'WARNING'},
                        f"Active collection '{sel_name}' doesn't start with 'c-'. Continuing and keeping name.")
            suffix = sel_name

        # Ensure 'RIMFILL' collection exists
        rimfill = bpy.data.collections.get("RIMFILL")
        if rimfill is None:
            rimfill = bpy.data.collections.new("RIMFILL")
            context.scene.collection.children.link(rimfill)

        # Append 'LightingSetup' collection from blend file
        try:
            with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
                if 'LightingSetup' in data_from.collections:
                    data_to.collections = ['LightingSetup']
                else:
                    self.report({'ERROR'}, "No 'LightingSetup' collection found in the blend file.")
                    return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load library: {e}")
            return {'CANCELLED'}

        # Rename appended collections to 'rm-' and link under RIMFILL
        renamed_any = False
        for coll in getattr(data_to, "collections", []):
            if coll is None:
                continue
            # Link under RIMFILL (not the scene root)
            ensure_root_child(rimfill, coll)

            # Rename safely
            target_name = unique_collection_name(f"rm-{suffix}")
            try:
                coll.name = target_name
                renamed_any = True
            except Exception as e:
                self.report({'WARNING'}, f"Could not rename appended collection: {e}")

        if not renamed_any:
            self.report({'WARNING'}, "Lighting setup appended but renaming may have failed.")

        self.report({'INFO'}, f"Lighting setup appended into 'RIMFILL' as 'rm-{suffix}'.")
        return {'FINISHED'}


def register():
    bpy.utils.register_class(LIGHTINGSETUP_OT_AppendBlend)


def unregister():
    bpy.utils.unregister_class(LIGHTINGSETUP_OT_AppendBlend)
