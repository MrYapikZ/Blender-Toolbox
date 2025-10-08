import bpy


# ------------------------------------------------------------------------
# Navigation Panel Properties
# ------------------------------------------------------------------------

def find_objects_by_key(key=""):
    override_objects = [obj for obj in bpy.data.objects if obj.override_library]
    return [o for o in override_objects if o.get(key)]


class LightingPropertiesUI:
    def __init__(self, layout, context):
        self.layout = layout
        self.context = context

    def draw(self):
        layout = self.layout
        s = self.context.scene
        props = s.lighting_props

        row = layout.row(align=True)
        row.operator("view3d.refresh_custom_prop_list", text="", icon="FILE_REFRESH")
        eevee = self.context.scene.eevee
        row.prop(eevee, "gtao_distance", text="AO Distance")

        key = props.key
        objs = sorted(find_objects_by_key(key), key=lambda o: o.name.lower())

        layout.label(text=f"Found: {len(objs)}")
        col = layout.column(align=True)
        if not objs:
            col.label(text="No objects with that key.", icon='INFO')
        else:
            for o in objs:
                box = layout.box()
                box.label(text=f"{o.name}", icon='OBJECT_DATA')

                # If it's a light, show its energy slider
                if o.type == 'LIGHT':
                    box.prop(o.data, "color", text="Color")
                    box.prop(o.data, "energy", text="Energy")
                    box.prop(o.data, "exposure", text="Exposure")
                    box.prop(o.data, "shadow_jitter_overblur", text="Shadow Jitter")
                else:
                    box.label(text="Not a Light object.", icon='ERROR')
                    box.label(text="Energy control is only available for lights.")
