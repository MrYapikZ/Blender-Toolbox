import bpy


# ------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------
def find_objects_by_key(key):
    return [obj for obj in bpy.data.objects if key in obj.keys()]


def get_compositor_tree(scene: bpy.types.Scene):
    """Return the scene's compositor node tree, or None safely."""
    if not scene:
        return None
    # In Blender 3.x/4.x, the compositor lives on the scene's node_tree
    tree = getattr(scene, "node_tree", None)
    return tree if tree and isinstance(tree, bpy.types.NodeTree) else None


def find_custom_node(scene: bpy.types.Scene, node_name):
    """Return the node with named if it exists."""
    tree = get_compositor_tree(scene)
    if not tree:
        return None
    return tree.nodes.get(node_name)


def get_thickness_socket(node: bpy.types.Node):
    """
    Return Occlusion_Thickness.inputs[0] exactly, or None if missing.
    """
    try:
        # You said this is the canonical path; we'll respect it but still guard it.
        node_exact = bpy.data.scenes["Scene"].node_tree.nodes.get("Occlusion_Thickness")
        if node_exact and len(node_exact.inputs) > 0:
            return node_exact.inputs[0]
    except Exception:
        pass
    return None


# ------------------------------------------------------------------------
# Navigation Panel Properties
# ------------------------------------------------------------------------
class LightingPropertiesUI:
    def __init__(self, layout, context):
        self.layout = layout
        self.context = context

    def draw(self):
        layout = self.layout
        s = self.context.scene
        props = s.lighting_props

        occ_box = layout.box()

        row_func = layout.row(align=True)
        row_func.operator("blp.make_override_lights_local", text="Override Light", icon="LIBRARY_DATA_OVERRIDE")
        # make func to detect bpy.data.scenes["Scene"].node_tree.nodes["Occlusion_Thickness"] exists or not

        col_ao = layout.column(align=True)
        col_ao.label(text="Ambient Occlusion Settings:")
        row_ao = layout.row(align=True)
        eevee = self.context.scene.eevee
        row_ao.prop(eevee, "gtao_distance", text="AO Distance")

        ao_thic_node = find_custom_node(s, "Occlusion_Thickness")
        if not ao_thic_node:
            occ_box.label(text="Compositor node 'Occlusion_Thickness' not found.", icon='ERROR')
        else:
            sock = get_thickness_socket(ao_thic_node)
            if not sock:
                occ_box.label(text="No suitable input socket on 'Occlusion_Thickness'.", icon='ERROR')
            else:
                # If linked, editing default_value won't affect output — still show for visibility
                if getattr(sock, "is_linked", False):
                    sub = occ_box.row(align=True)
                    sub.enabled = False
                    sub.prop(sock, "default_value", text="AO Thickness")
                    occ_box.label(text="Input is linked; driven upstream.", icon='DECORATE_LINKED')
                else:
                    row_ao.prop(sock, "default_value", text="AO Thickness")
        col_mist_range = layout.column(align=True)
        col_mist_range.label(text="Mist Range:")
        row_mist_range_1 = layout.row(align=True)
        row_mist_range_2 = layout.row(align=True)

        mist_range_node = find_custom_node(s, "Mist_Range")
        if not mist_range_node:
            occ_box.label(text="Compositor node 'Mist_Range' not found.", icon='ERROR')
        else:
            row_mist_range_1.prop(mist_range_node.inputs[1], "default_value", text="From Min")
            row_mist_range_1.prop(mist_range_node.inputs[2], "default_value", text="From Max")
            row_mist_range_2.prop(mist_range_node.inputs[3], "default_value", text="To Min")
            row_mist_range_2.prop(mist_range_node.inputs[4], "default_value", text="To Max")

        col_mist_intensity = layout.column(align=True)
        col_mist_intensity.label(text="Mist Intensity Ramp:")

        mist_intensity_node = find_custom_node(s, "Mist_Intensity")
        if not mist_intensity_node:
            occ_box.label(text="Compositor node 'Mist_Intensity' not found.", icon='ERROR')
        else:
            layout.template_color_ramp(mist_intensity_node, "color_ramp", expand=True)

        key = props.key
        objs = sorted(find_objects_by_key(key), key=lambda o: o.name.lower())

        layout.label(text=f"Found: {len(objs)}")
        col = layout.column(align=True)
        if not objs:
            col.label(text="No objects with that key.", icon='INFO')
        else:
            for o in objs:
                box = layout.box()
                box.label(text=f"{o.get(key)}", icon='LIGHT_DATA')

                # If it's a light, show its energy slider
                if o.type == 'LIGHT':
                    box.prop(o.data, "color", text="Color")
                    box.prop(o.data, "energy", text="Energy")
                    box.prop(o.data, "exposure", text="Exposure")
                    box.prop(o.data, "shadow_jitter_overblur", text="Shadow Jitter")
                elif o.type == 'EMPTY':
                    name_l = o.get(key).lower()

                    if name_l.startswith("light_aim"):
                        # Z position: location is a Vector property; use index=2 for Z
                        box.prop(o, "location", index=2, text="Aim Z Location")

                    elif name_l.startswith("light_root"):
                        # Z rotation: show Euler Z. (Works even if current mode is quaternion—Blender will use Euler here.)
                        # Optional: remind current mode
                        if o.rotation_mode not in {'XYZ', 'XZY', 'YXZ', 'YZX', 'ZXY', 'ZYX'}:
                            box.label(text=f"Rotation mode: {o.rotation_mode}", icon='INFO')

                        box.prop(o, "rotation_euler", index=2, text="Root Z Rotation")

                    else:
                        box.label(text="Empty (not light_aim/root)")
                else:
                    box.label(text="Not a Light object.", icon='ERROR')
                    box.label(text="Energy control is only available for lights.")
