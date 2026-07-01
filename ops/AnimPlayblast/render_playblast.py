import bpy


class APB_OT_Render(bpy.types.Operator):
    bl_idname = "apb.render_playblast"
    bl_label = "Render Playblast"
    bl_description = "Render Animation Playblast"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bpy.ops.apb.apply_preset()

        original_start = bpy.context.scene.frame_start
        original_end = bpy.context.scene.frame_end

        start_frame = original_start
        end_frame = original_end

        for marker in bpy.context.scene.timeline_markers:
            if marker.name == "EX_START":
                start_frame = marker.frame
            elif marker.name == "EX_END":
                end_frame = marker.frame

        bpy.context.scene.frame_start = start_frame
        bpy.context.scene.frame_end = end_frame

        camera = bpy.context.scene.camera
        if camera:
            camera.select_set(True)
            bpy.context.view_layer.objects.active = camera
            bpy.ops.render.opengl(animation=True)
        else:
            print("No camera found in the scene.")
            self.report({'ERROR'}, "No camera found in the scene.")
            return {'CANCELLED'}

        bpy.context.scene.frame_start = original_start
        bpy.context.scene.frame_end = original_end
        bpy.ops.apb.clear_render_markers()
        bpy.ops.apb.return_solid()
        bpy.ops.apb.view_camera_operator_default()

        self.report({'INFO'}, "Rendering completed.")
        return {'FINISHED'}


def register():
    bpy.utils.register_class(APB_OT_Render)


def unregister():
    bpy.utils.unregister_class(APB_OT_Render)
