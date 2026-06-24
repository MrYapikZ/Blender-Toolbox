import bpy


# ------------------------------------------------------------------------
# ExConfig Drive
# ------------------------------------------------------------------------
class ExConfigDriveUI(bpy.types.Panel):
    bl_label = "DelthλConfig Drive"
    bl_idname = "EXCONFIG_DRIVE_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'ExToolbox'
    bl_description = "Drive DelthλConfig settings"
    bl_parent_id = "EXCONFIG_PT_panel"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 1

    def draw(self, context):
        layout = self.layout
        s = context.scene

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Drive DelthλConfig.", icon='PREFERENCES')
        col.prop(s.exconfig, "project_drive_prod", text="Prod")
        col.prop(s.exconfig, "project_drive_output", text="Output")


# def register():
#     bpy.utils.register_class(ExConfigDriveUI)


# def unregister():
#     bpy.utils.unregister_class(ExConfigDriveUI)
