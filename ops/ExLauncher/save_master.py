import bpy
from pathlib import Path
from ...utils.file_manager import FileManager


# ------------------------------------------------------------------------
# Save Progress Operator
# ------------------------------------------------------------------------
class EXLAUNCHER_OT_SaveMaster(bpy.types.Operator):
    bl_idname = "exlauncher.save_master"
    bl_label = "Save Master"
    bl_description = "Save current progress to master in ExLauncher"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        exlauncer = scene.exlauncher

        if not bpy.data.filepath:
            self.report({'ERROR'}, "Please save the Blender file before saving progress.")
            return {'CANCELLED'}

        project_path = Path(bpy.data.filepath)
        project_dir = project_path.parent

        latest_file = FileManager.get_latest_versioned_file(project_dir)

        if not latest_file:
            self.report({'ERROR'}, "No versioned .blend files found.")
            return {'CANCELLED'}

        next_path = FileManager.next_version_name(latest_file)

        bpy.ops.wm.save_mainfile(copy=False, increment=True)

        if exlauncer.version_type == 'LAST_NUMBER':
            master_file = FileManager.remove_trailing_number_from_last_underscore(str(next_path))
        else:
            master_file = FileManager.remove_last_underscore(str(next_path))

        bpy.ops.wm.save_as_mainfile(filepath=str(master_file), copy=True)

        self.report({'INFO'}, f"Master saved to '{master_file}' and progress saved to '{next_path}'")
        return {'FINISHED'}


def register():
    bpy.utils.register_class(EXLAUNCHER_OT_SaveMaster)


def unregister():
    bpy.utils.unregister_class(EXLAUNCHER_OT_SaveMaster)
