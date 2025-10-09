import bpy, re
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


def unique_collection_name(base: str, reporter=None) -> str | None:
    """
    Return base if it's available.
    If a collection with that name already exists, return None and optionally warn.
    """
    if bpy.data.collections.get(base) is None:
        return base

    # base name already taken → stop and warn
    if reporter:
        reporter({'WARNING'}, f"Collection '{base}' already exists. Aborting to avoid conflict.")
    return None

def object_name_with_suffix(name: str, suffix: str) -> str:
    """
    Insert _<suffix> before any numeric .### tail.
    If already suffixed with _<suffix>, return unchanged.
    """
    wanted_tail = f"_{suffix}"
    if name.endswith(wanted_tail) or re.search(rf"_{re.escape(suffix)}\.\d{{3}}$", name):
        return name  # already has suffix (with or without numeric tail)

    m = re.match(r"^(.*?)(\.\d{3})$", name)
    if m:
        core, num = m.groups()
        return f"{core}{wanted_tail}{num}"
    return f"{name}{wanted_tail}"

def unique_object_name(desired: str) -> str:
    """Ensure object name is unique across bpy.data.objects."""
    if bpy.data.objects.get(desired) is None:
        return desired
    i = 1
    while True:
        cand = f"{desired}.{i:03d}"
        if bpy.data.objects.get(cand) is None:
            return cand
        i += 1

def add_suffix_to_objects_in_collection(coll: bpy.types.Collection, suffix: str) -> int:
    """
    Rename all objects inside `coll` (recursively) by appending _<suffix>.
    Returns the count of objects renamed.
    """
    renamed = 0
    # coll.all_objects includes objects from nested child collections
    objs = getattr(coll, "all_objects", coll.objects)
    for obj in objs:
        old = obj.name
        wanted = object_name_with_suffix(old, suffix)
        if wanted != old:
            new_name = unique_object_name(wanted)
            try:
                obj.name = new_name
                renamed += 1
            except Exception:
                # Silently skip if renaming is blocked by some operator context
                pass
    return renamed

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

        # Rename appended collections to 'rf-' and link under RIMFILL
        renamed_any = False
        for coll in getattr(data_to, "collections", []):
            if coll is None:
                continue
            # Link under RIMFILL (not the scene root)
            ensure_root_child(rimfill, coll)

            # Rename collection to 'rf-<suffix>'
            target_name = unique_collection_name(f"rf-{suffix}")
            try:
                coll.name = target_name
                renamed_any = True
            except Exception as e:
                self.report({'WARNING'}, f"Could not rename appended collection: {e}")

            # Rename all objects inside the collection to include _<suffix>
            renamed_count = add_suffix_to_objects_in_collection(coll, suffix)
            if renamed_count:
                self.report({'INFO'}, f"Renamed {renamed_count} object(s) to include _{suffix}.")
            else:
                self.report({'INFO'}, f"No object names needed _{suffix} (already suffixed or none found).")

        if not renamed_any:
            self.report({'WARNING'}, "Lighting setup appended but renaming may have failed.")

        self.report({'INFO'}, f"Lighting setup appended into 'RIMFILL' as 'rm-{suffix}'.")
        return {'FINISHED'}


def register():
    bpy.utils.register_class(LIGHTINGSETUP_OT_AppendBlend)


def unregister():
    bpy.utils.unregister_class(LIGHTINGSETUP_OT_AppendBlend)
