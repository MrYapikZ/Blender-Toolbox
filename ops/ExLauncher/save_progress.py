import bpy
from pathlib import Path
from ...utils.file_manager import FileManager


# ------------------------------------------------------------------------
# Save Progress Operator
# ------------------------------------------------------------------------
class EXLAUNCHER_OT_SaveProgress(bpy.types.Operator):
    bl_idname = "exlauncher.save_progress"
    bl_label = "Save Progress"
    bl_description = "Save current progress in ExLauncher"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if not bpy.data.filepath:
            self.report({'ERROR'}, "Please save the Blender file before saving progress.")
            return {'CANCELLED'}

        bpy.ops.wm.save_mainfile(increment=True)

        self.report({'INFO'}, f"Progress saved for project '{next_path}'")
        return {'FINISHED'}


def register():
    bpy.utils.register_class(EXLAUNCHER_OT_SaveProgress)


def unregister():
    bpy.utils.unregister_class(EXLAUNCHER_OT_SaveProgress)
