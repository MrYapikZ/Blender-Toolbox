from . import add_sphere

modules = [
    add_sphere
]


def register():
    for item in modules:
        item.register()


def unregister():
    for item in modules:
        item.unregister()
