import bpy


# ------------------------------------------------------------------------
# Navigation Properties
# ------------------------------------------------------------------------
class Toolbox(bpy.types.PropertyGroup):
    ui_mode: bpy.props.EnumProperty(
        name="Mode",
        description="Choose which tool page to display",
        items=[
            ("INFO", "Info", "Information about the addon"),
            ("LIGHTING_PROPERTIES", "LightingProperties", "Lighting override controls"),
            ("LIGHTING_SETUP", "LightingSetup", "Lighting setup tools"),
            ("ANIM_PLAYBLAST", "AnimPlayblast", "Animation playblast tools"),
            ("IMG_WIN_PATH", "ImgWinPath", "Image path management tools"),
            ("ASSET_COL_RENAME", "AssetColRename", "Asset collection rename tools"),
            (
                "IMPORT_VFX_PLANE",
                "ImportVfxPlane",
                "Import movie or image sequence as plane with correct settings",
            ),
            ("PROXYFY", "Proxyfy", "I don't know"),
            ("SHADOWCATCHER", "ShadowCatcher", "Add gobos to object")
        ],
        default="INFO",
    )
    show_exconfig: bpy.props.BoolProperty(
        name="Show ExConfig Options",
        description="Toggle to show or hide ExConfig related options",
        default=False,
    )
    version: bpy.props.StringProperty(
        name="Version", default="0.2.13", options={"HIDDEN"}
    )


class ToolboxCompositing(bpy.types.PropertyGroup):
    ui_mode: bpy.props.EnumProperty(
        name="Mode",
        description="Choose which tool page to display",
        items=[
            ("INFO", "Info", "Information about the addon"),
            (
                "EYE_GLOW_COMPOSITING",
                "EyeGlowCompositing",
                "Eye glow compositing tools",
            ),
        ],
        default="INFO",
    )


def register():
    bpy.utils.register_class(Toolbox)
    bpy.utils.register_class(ToolboxCompositing)
    bpy.types.Scene.toolbox = bpy.props.PointerProperty(type=Toolbox)
    bpy.types.Scene.toolbox_compositing = bpy.props.PointerProperty(
        type=ToolboxCompositing
    )


def unregister():
    bpy.utils.unregister_class(Toolbox)
    bpy.utils.unregister_class(ToolboxCompositing)
    del bpy.types.Scene.toolbox
    del bpy.types.Scene.toolbox_compositing
