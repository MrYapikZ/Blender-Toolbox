import bpy
from .GraphNewWindow import GraphNewWindowPrefUI

try:
    # Prefer the constant from the root package if you defined it there
    from pref import ADDON_ID  # in __init__.py set: ADDON_ID = __name__
except Exception:
    # Fallback to the top-level package name
    ADDON_ID = (__package__.split('.', 1)[0] if __package__
                else __name__.split('.', 1)[0])


# ------------------------------------------------------------------------
# AddOn Preferences
# ------------------------------------------------------------------------
class AddOnPreferences(bpy.types.AddonPreferences):
    bl_idname = ADDON_ID

    def draw(self, context):
        layout = self.layout

        # Draw the Graph New Window preferences UI
        GraphNewWindowPrefUI(layout, context).draw()


def register():
    bpy.utils.register_class(AddOnPreferences)


def unregister():
    bpy.utils.unregister_class(AddOnPreferences)
