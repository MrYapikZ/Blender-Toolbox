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
    only_selected: bpy.props.BoolProperty(
        name="Only Selected Objects",
        description="Process only currently selected objects instead of scanning all objects",
        default=True,
    )
    purge_unreferenced: bpy.props.BoolProperty(
        name="Purge Unreferenced Linked Lights",
        description="After making copies, remove any linked Light datablocks with zero users",
        default=True,
    )


def register():
    bpy.utils.register_class(LightingProperties)
    bpy.types.Scene.lighting_props = bpy.props.PointerProperty(type=LightingProperties)


def unregister():
    bpy.utils.unregister_class(LightingProperties)
    del bpy.types.Scene.lighting_props
