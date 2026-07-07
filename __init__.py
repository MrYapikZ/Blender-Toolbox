bl_info = {
    "name": "DelthλTools",
    "description": "Tools for Blender",
    "author": "Yapi",
    "version": (0, 2, 13),
    "blender": (4, 5, 0),
}

import bpy, os
from . import ui, pref, ops, addon

ADDON_ID = __name__
ADDON_DIR = os.path.dirname(__file__)


# ------------------------------------------------------------------------
# Register
# ------------------------------------------------------------------------

modules = [
    pref,
    ops,
    addon,
    ui,
]


def register():
    for item in modules:
        item.register()


def unregister():
    for item in modules:
        item.unregister()
