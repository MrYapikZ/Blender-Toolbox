import bpy
from collections import defaultdict
from ...utils.json_manager import JSONManager


# ------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------
def find_objects_by_key(key: str):
    """All objects that have the given custom property key."""
    return [obj for obj in bpy.data.objects if key in obj.keys()]


# ------------------------------------------------------------------------
# Lighting Properties - Export/Import Preset
# ------------------------------------------------------------------------
class ExportLightingPresetOperator(bpy.types.Operator):
    """Export current lighting settings to a preset file"""
    bl_idname = "blp.export_lighting_preset"
    bl_label = "Export Lighting Preset"
    bl_options = {'REGISTER', 'UNDO'}

    # File browser props
    filepath: bpy.props.StringProperty(subtype='FILE_PATH')
    filter_glob: bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'}
    )

    def invoke(self, context, event):
        s = context.scene
        props = s.lighting_props
        key = getattr(props, "key", "") or "lighting_preset"

        # Default to blend-file folder with a sensible name
        default_name = f"{key}.json"
        self.filepath = bpy.path.abspath(f"//{default_name}")

        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        s = context.scene
        props = s.lighting_props
        key = props.key

        # Get light objects
        lights = [o for o in find_objects_by_key(key) if o.type == 'LIGHT' and getattr(o, "data", None)]

        # Prepare payload
        by_collection = defaultdict(list)
        for o in lights:
            # Get parent collection name (handle cases where object may not belong to a collection)
            parent_collection = o.users_collection[0].name if o.users_collection else "NoCollection"

            # Light data
            col = tuple(float(c) for c in o.data.color[:3])
            energy = float(o.data.energy)
            exposure = float(o.data.exposure)
            shadow_jitter_overblur = float(o.data.shadow_jitter_overblur)

            by_collection[parent_collection].append({
                "name": o.name,
                "color": col,
                "energy": energy,
                "exposure": exposure,
                "shadow_jitter_overblur": shadow_jitter_overblur,
            })

        payload = [{"collection": cname, "preset": items} for cname, items in by_collection.items()]

        # Resolve/ensure path
        path = self.filepath or ""
        if not path:
            self.report({'ERROR'}, "No file path selected.")
            return {'CANCELLED'}
        if not path.lower().endswith(".json"):
            path += ".json"
        abs_path = bpy.path.abspath(path)

        JSONManager.save_json(data=payload, filepath=abs_path)

        return {'FINISHED'}

class ImportLightingPresetOperator(bpy.types.Operator):
    """Import lighting settings from a preset file"""
    bl_idname = "blp.import_lighting_preset"
    bl_label = "Import Lighting Preset"
    bl_options = {'REGISTER', 'UNDO'}

    # File browser props
    filepath: bpy.props.StringProperty(subtype='FILE_PATH')
    filter_glob: bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'}
    )

    def invoke(self, context, event):
        s = context.scene
        props = s.lighting_props
        key = getattr(props, "key", "") or "lighting_preset"

        # Default to blend-file folder with a sensible name
        default_name = f"{key}.json"
        self.filepath = bpy.path.abspath(f"//{default_name}")

        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        s = context.scene
        props = s.lighting_props
        key = props.key

        # Resolve path
        path = bpy.path.abspath(self.filepath)
        data = JSONManager.load_json(filepath=path)
        if data is None:
            self.report({'ERROR'}, f"Failed to load preset from {path}")
            return {'CANCELLED'}

        # Get light objects
        applied = 0
        skipped = 0

        for entry in data:
            collection_name = entry.get("collection", "")
            preset_items = entry.get("preset", [])
            if not collection_name or not preset_items:
                continue

            # Find collection
            collection = bpy.data.collections.get(collection_name)
            if not collection:
                self.report({'WARNING'}, f"Collection '{collection_name}' not found; skipping.")
                skipped += len(preset_items)
                continue

            # Apply presets to lights in the collection
            for item in preset_items:
                light_name = item.get("name", "")
                if not light_name:
                    continue
                light_obj = collection.objects.get(light_name)
                if not light_obj or light_obj.type != 'LIGHT' or getattr(light_obj, "data", None) is None:
                    skipped += 1
                    continue

                # Apply properties
                light_data = light_obj.data
                light_data.color = item.get("color", (1.0, 1.0, 1.0))
                light_data.energy = item.get("energy", 10.0)
                light_data.exposure = item.get("exposure", 0.0)
                light_data.shadow_jitter_overblur = item.get("shadow_jitter_overblur", 0.0)
                applied += 1

        return {'FINISHED'}

def register():
    bpy.utils.register_class(ImportLightingPresetOperator)
    bpy.utils.register_class(ExportLightingPresetOperator)
def unregister():
    bpy.utils.unregister_class(ImportLightingPresetOperator)
    bpy.utils.unregister_class(ExportLightingPresetOperator)