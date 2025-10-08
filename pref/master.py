import bpy


# ------------------------------------------------------------------------
# Navigation Properties
# ------------------------------------------------------------------------
class Toolbox(bpy.types.PropertyGroup):
    ui_mode: bpy.props.EnumProperty(
        name="Mode",
        description="Choose which tool page to display",
        items=[
            ('TOOLS', "Tools", "General utilities, version and shortcuts"),
            ('LIGHTING', "LightingProperties", "Lighting override controls"),
        ],
        default='TOOLS',
    )
    version: bpy.props.StringProperty(
        name="Version",
        default="0.1.0",
        options={'HIDDEN'}
    )


def register():
    bpy.utils.register_class(Toolbox)
    bpy.types.Scene.toolbox = bpy.props.PointerProperty(type=Toolbox)


def unregister():
    bpy.utils.unregister_class(Toolbox)
    del bpy.types.Scene.toolbox
