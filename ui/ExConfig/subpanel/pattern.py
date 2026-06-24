import bpy


# ------------------------------------------------------------------------
# ExConfig Pattern
# ------------------------------------------------------------------------
class ExConfigPatternUI(bpy.types.Panel):
    bl_label = "DelthλConfig Pattern"
    bl_idname = "EXCONFIG_PATTERN_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'ExToolbox'
    bl_description = "Pattern DelthλConfig settings"
    bl_parent_id = "EXCONFIG_PT_panel"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 2

    def draw(self, context):
        layout = self.layout
        s = context.scene

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Pattern DelthλConfig.", icon='PREFERENCES')
        col.prop(s.exconfig, "project_pattern_division", text="Division")
        col.prop(s.exconfig, "project_pattern_base", placeholder="e.g. /mnt/X/date_project_name/pipeline/division/", text="Base")
        col.prop(s.exconfig, "project_pattern_example", placeholder="e.g. /mnt/X/date_project_name/pipeline/division/epXXX/epXXX_sqXX/epXXX_sqXX_shXXXX/progress/mdt_epXXX_sqXX_shXXXX_divisioncode_vXXXX.extension", text="Example")


def register():
    bpy.utils.register_class(ExConfigPatternUI)


def unregister():
    bpy.utils.unregister_class(ExConfigPatternUI)
