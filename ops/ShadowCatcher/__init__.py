from . import shadow_catcher_cloth

modules = [
    shadow_catcher_cloth,
]


def register():
    for item in modules:
        item.register()


def unregister():
    for item in modules:
        item.unregister()
