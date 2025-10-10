from . import master, lighting_properties, lighting_setup

modules = [
    master,
    lighting_properties,
    lighting_setup,
]


def register():
    for item in modules:
        item.register()


def unregister():
    for item in modules:
        item.unregister()
