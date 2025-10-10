import bpy


# ------------------------------------------------------------------------
# Lighting Setup - Append Blend File
# ------------------------------------------------------------------------
class LIGHTINGSETUP(bpy.types.PropertyGroup):
    filepath: bpy.props.StringProperty(
        name="File Path",
        description="Path to the blend file to append from",
        default="presets/blend/lighting_setup.blend",
        subtype='FILE_PATH'
    )


def register():
    bpy.utils.register_class(LIGHTINGSETUP)
    bpy.types.Scene.lighting_setup = bpy.props.PointerProperty(type=LIGHTINGSETUP)


def unregister():
    bpy.utils.unregister_class(LIGHTINGSETUP)
    del bpy.types.Scene.lighting_setup
