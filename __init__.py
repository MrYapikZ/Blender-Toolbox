bl_info = {
    "name": "MXTools",
    "description": "Tools for Blender",
    "author": "MrYapikZ",
    "version": (0, 1, 11),
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
