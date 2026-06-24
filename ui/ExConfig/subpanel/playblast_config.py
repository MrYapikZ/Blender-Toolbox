import bpy


# ------------------------------------------------------------------------
# ExConfig Playblast Config
# ------------------------------------------------------------------------
class ExConfigPlayblastConfigUI(bpy.types.Panel):
    bl_label = "DelthλConfig Playblast"
    bl_idname = "EXCONFIG_PLAYBLAST_CONFIG_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'ExToolbox'
    bl_description = "Playblast preset configuration path"
    bl_parent_id = "EXCONFIG_PT_panel"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 4

    def draw(self, context):
        layout = self.layout
        s = context.scene

        box = layout.box()
        col = box.column(align=True)
        col.label(text="Playblast Preset Config", icon='FILE_MOVIE')
        col.prop(s.exconfig, "playblast_config", placeholder="e.g. /mnt/X/date_project_name/00_tools/01_preset_script/delta_config_playblast.json", text="Config Path")
        col.prop(s.exconfig, "safe_area_path", text="Safe Area Path")
        
        # Show warning if path is empty or invalid
        if not s.exconfig.playblast_config:
            col.label(text="No config file set", icon='ERROR')
        else:
            import os
            if not os.path.exists(s.exconfig.playblast_config):
                col.label(text="File not found", icon='ERROR')
            else:
                col.label(text="Config file found", icon='CHECKMARK')


def register():
    bpy.utils.register_class(ExConfigPlayblastConfigUI)


def unregister():
    bpy.utils.unregister_class(ExConfigPlayblastConfigUI)
