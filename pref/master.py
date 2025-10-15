import bpy


# ------------------------------------------------------------------------
# Navigation Properties
# ------------------------------------------------------------------------
class Toolbox(bpy.types.PropertyGroup):
    ui_mode: bpy.props.EnumProperty(
        name="Mode",
        description="Choose which tool page to display",
        items=[
            ('INFO', "Info", "Information about the addon"),
            ('LIGHTING_PROPERTIES', "LightingProperties", "Lighting override controls"),
            ('LIGHTING_SETUP', "LightingSetup", "Lighting setup tools"),
        ],
        default='INFO',
    )
    version: bpy.props.StringProperty(
        name="Version",
        default="0.1.7",
        options={'HIDDEN'}
    )


def register():
    bpy.utils.register_class(Toolbox)
    bpy.types.Scene.toolbox = bpy.props.PointerProperty(type=Toolbox)


def unregister():
    bpy.utils.unregister_class(Toolbox)
    del bpy.types.Scene.toolbox
