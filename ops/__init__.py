from . import LightingProperties, LightingSetup

modules = [
    LightingProperties,
    LightingSetup,
]


def register():
    for item in modules:
        item.register()


def unregister():
    for item in modules:
        item.unregister()
