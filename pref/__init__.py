from . import master, lighting_properties

modules = [
    master,
    lighting_properties,
]


def register():
    for item in modules:
        item.register()


def unregister():
    for item in modules:
        item.unregister()
