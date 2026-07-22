import bpy

from .LightingProperties import LightingPropertiesUI
from .LightingSetup import LightingSetupUI
from .EyeGlowCompositing import EyeGlowCompositingUI
from .AnimPlayblast import AnimPlayblastUI
from .ImgWinPath import ImgWinPathUI
from .AssetColRename import AssetColRenameUI
from .ImportVfxPlane import ImportVfxPlaneUI
from .Proxyfy import ProxyfyUI
from .ShadowCatcher import ShadowCatcherUI
from .AnimMisc import AnimMiscUI


# ------------------------------------------------------------------------
# Navigation Panel Properties
# ------------------------------------------------------------------------
class NAV_PT_Panel(bpy.types.Panel):
    bl_label = "DelthλTools"
    bl_idname = "EXTOOLBOX_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'DelthλTools'
    bl_description = "Navigation panel for MasterX Tools"

    def draw(self, context):
        layout = self.layout
        s = context.scene

        # Top combobox
        row = layout.row(align=True)
        row.prop(s.toolbox, "ui_mode", text="Mode", expand=False)

        layout.separator(factor=0.3)

        if s.toolbox.ui_mode == 'INFO':
            # Header: version + quick info
            box = layout.box()
            col = box.column(align=True)
            col.label(text=f"DelthλTools v{s.toolbox.version}", icon='INFO')
            col.label(text="Maintainer: Yapi")
        elif s.toolbox.ui_mode == 'LIGHTING_PROPERTIES':
            LightingPropertiesUI(self.layout, context).draw()
        elif s.toolbox.ui_mode == 'LIGHTING_SETUP':
            LightingSetupUI(self.layout, context).draw()
        elif s.toolbox.ui_mode == 'ANIM_PLAYBLAST':
            AnimPlayblastUI(self.layout, context).draw()
        elif s.toolbox.ui_mode == 'IMG_WIN_PATH':
            ImgWinPathUI(self.layout, context).draw()
        elif s.toolbox.ui_mode == 'ASSET_COL_RENAME':
            AssetColRenameUI(self.layout, context).draw()
        elif s.toolbox.ui_mode == 'IMPORT_VFX_PLANE':
            ImportVfxPlaneUI(self.layout, context).draw()
        elif s.toolbox.ui_mode == 'PROXYFY':
            ProxyfyUI(self.layout, context).draw()
        elif s.toolbox.ui_mode == 'SHADOWCATCHER':
            ShadowCatcherUI(self.layout, context).draw()
        elif s.toolbox.ui_mode == 'ANM_MISC':
            AnimMiscUI(self.layout, context).draw()


class NAV_PT_PanelCompositing(bpy.types.Panel):
    bl_label = "DelthλTools"
    bl_idname = "EXTOOLBOX_PT_panel_compositing"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'DelthλTools'
    bl_description = "Compositing panel for MasterX Tools"

    def draw(self, context):
        layout = self.layout
        s = context.scene

        # Top combobox
        row = layout.row(align=True)
        row.prop(s.toolbox_compositing, "ui_mode", text="Mode", expand=False)

        layout.separator(factor=0.3)

        if s.toolbox_compositing.ui_mode == 'INFO':
            # Header: version + quick info
            box = layout.box()
            col = box.column(align=True)
            col.label(text=f"DelthλTools v{s.toolbox.version}", icon='INFO')
            col.label(text="Maintainer: Yapi")
        elif s.toolbox_compositing.ui_mode == 'EYE_GLOW_COMPOSITING':
            EyeGlowCompositingUI(self.layout, context).draw()


# ------------------------------------------------------------------------
# Register
# ------------------------------------------------------------------------
def register():
    bpy.utils.register_class(NAV_PT_Panel)
    bpy.utils.register_class(NAV_PT_PanelCompositing)


def unregister():
    bpy.utils.unregister_class(NAV_PT_Panel)
    bpy.utils.unregister_class(NAV_PT_PanelCompositing)
