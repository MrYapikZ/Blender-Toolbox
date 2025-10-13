bl_info = {
    "name": "MXTools",
    "description": "Tools for Blender",
    "author": "MrYapikZ",
    "version": (0, 1, 3),
    "blender": (4, 5, 0),
}

import bpy, os
from . import ui, pref, ops

ADDON_ID = __name__
ADDON_DIR = os.path.dirname(__file__)


# ------------------------------------------------------------------------
# Register
# ------------------------------------------------------------------------

modules = [
    pref,
    ops,
    ui,
]


def register():
    for item in modules:
        item.register()


def unregister():
    for item in modules:
        item.unregister()
