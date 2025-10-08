import bpy


# ------------------------------------------------------------------------
# Navigation Properties
# ------------------------------------------------------------------------
class LightingProperties(bpy.types.PropertyGroup):
    key: bpy.props.StringProperty(
        name="Custom Property Key",
        description="List objects that have this custom property key",
        default="blp",
    )


def register():
    bpy.utils.register_class(LightingProperties)
    bpy.types.Scene.lighting_props = bpy.props.PointerProperty(type=LightingProperties)


def unregister():
    bpy.utils.unregister_class(LightingProperties)
    del bpy.types.Scene.lighting_props
