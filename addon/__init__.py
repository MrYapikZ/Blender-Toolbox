from . import pref, GraphNewWindow

modules = [
    GraphNewWindow,
    pref,
]


def register():
    for item in modules:
        item.register()


def unregister():
    for item in modules:
        item.unregister()
