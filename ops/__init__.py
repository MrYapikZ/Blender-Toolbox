from . import LightingProperties, LightingSetup, GraphNewWindow, EyeGlowCompositing, AnimPlayblast, ExConfig, \
    ImgWinPath, ExLauncher, AssetColRename, ImportVfxPlane, Proxyfy, ShadowCatcher, AnimMisc

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
    ShadowCatcher,
    AnimMisc
]


def register():
    for item in modules:
        item.register()


def unregister():
    for item in modules:
        item.unregister()
