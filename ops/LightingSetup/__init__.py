from . import append_blend, set_child_of_bone_popup

modules = [
    set_child_of_bone_popup,
    append_blend,
]


def register():
    for item in modules:
        item.register()


def unregister():
    for item in modules:
        item.unregister()
