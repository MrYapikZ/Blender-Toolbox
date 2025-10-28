from . import open_new_window

modules = [
    open_new_window
]

def register():
    for item in modules:
        item.register()

def unregister():
    for item in modules:
        item.unregister()