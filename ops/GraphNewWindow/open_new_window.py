import bpy


# ------------------------------------------------------------------------
# Graph New Window - Operator
# ------------------------------------------------------------------------
class OT_GraphNewWindow(bpy.types.Operator):
    bl_idname = "gnw.graph_new_window"
    bl_label = "Graph New Window"
    bl_description = "Open a new window with the Graph Editor"

    def execute(self, context):
        # Create a new window
        new_window = bpy.ops.wm.window_new()
        # Set the area type to Graph Editor
        for area in bpy.context.window_manager.windows[-1].screen.areas:
            if area.type == 'GRAPH_EDITOR':
                break
        else:
            for area in bpy.context.window_manager.windows[-1].screen.areas:
                if area.type == 'VIEW_3D':
                    area.type = 'GRAPH_EDITOR'
                    break
        return {'FINISHED'}


def register():
    bpy.utils.register_class(OT_GraphNewWindow)


def unregister():
    bpy.utils.unregister_class(OT_GraphNewWindow)
