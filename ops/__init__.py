from . import LightingProperties, LightingSetup, GraphNewWindow, EyeGlowCompositing, AnimPlayblast, ExConfig, \
    ImgWinPath, ExLauncher, AssetColRename, ImportVfxPlane, Proxyfy, ShadowCatcher

modules = [
    ExConfig,
    ExLauncher,
    LightingProperties,
    LightingSetup,
    GraphNewWindow,
    EyeGlowCompositing,
    AnimPlayblast,
    ImgWinPath,
    AssetColRename,
    ImportVfxPlane,
    Proxyfy,
    ShadowCatcher
]


def register():
    for item in modules:
        item.register()


def unregister():
    for item in modules:
        item.unregister()
