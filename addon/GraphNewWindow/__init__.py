from . import panel

GraphNewWindowPrefUI = panel.GraphNewWindowPrefUI

modules = [
    panel
]


def register():
    for item in modules:
        item.register()


def unregister():
    for item in modules:
        item.unregister()
