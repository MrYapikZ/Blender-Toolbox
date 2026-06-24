import bpy


# ------------------------------------------------------------------------
# ExConfig Basic
# ------------------------------------------------------------------------
class ExConfigBasicUI(bpy.types.Panel):
    bl_label = "DelthλConfig Basic"
    bl_idname = "EXCONFIG_BASIC_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'ExToolbox'
    bl_description = "Basic DelthλConfig settings"
    bl_parent_id = "EXCONFIG_PT_panel"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 0

    def draw(self, context):
        layout = self.layout
        s = context.scene

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Basic DelthλConfig.", icon='PREFERENCES')
        col.prop(s.exconfig, "project_name", placeholder="e.g. MyProject", text="Name")
        col.prop(s.exconfig, "project_code", placeholder="e.g. PRJ", text="Code")


def register():
    bpy.utils.register_class(ExConfigBasicUI)


def unregister():
    bpy.utils.unregister_class(ExConfigBasicUI)
