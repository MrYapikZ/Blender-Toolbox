import bpy

from .LightingProperties import LightingPropertiesUI


# ------------------------------------------------------------------------
# Navigation Panel Properties
# ------------------------------------------------------------------------
class NAV_PT_Panel(bpy.types.Panel):
    bl_label = "MXTools"
    bl_idname = "NAV_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'MXTools'
    bl_description = "Navigation panel for MasterX Tools"

    def draw(self, context):
        layout = self.layout
        s = context.scene

        # Top combobox
        row = layout.row(align=True)
        row.prop(s.toolbox, "ui_mode", text="Mode", expand=False)

        layout.separator(factor=0.3)

        if s.toolbox.ui_mode == 'TOOLS':
            # Header: version + quick info
            box = layout.box()
            row = box.row(align=True)
            row.label(text=f"Toolkit v{s.toolbox.version}", icon='INFO')
        elif s.toolbox.ui_mode == 'LIGHTING':
            LightingPropertiesUI(self.layout, context).draw()


# ------------------------------------------------------------------------
# Register
# ------------------------------------------------------------------------
def register():
    bpy.utils.register_class(NAV_PT_Panel)


def unregister():
    bpy.utils.unregister_class(NAV_PT_Panel)
