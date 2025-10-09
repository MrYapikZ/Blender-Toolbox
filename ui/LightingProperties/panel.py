import bpy
from collections import defaultdict


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


def _suffix_of(s: str) -> str:
    if not s:
        return ""
    return s.rsplit('_', 1)[-1]  # after last underscore


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

        col_defocus_zscale = layout.column(align=True)
        col_defocus_zscale.label(text="Defocus Z-Scale:")
        defocus_zscale_node = find_custom_node(s, "Defocus")
        if not defocus_zscale_node:
            occ_box.label(text="Compositor node 'Defocus' not found.", icon='ERROR')
        else:
            col_defocus_zscale.prop(defocus_zscale_node, "z_scale", text="Z-Scale")

        key = props.key
        objs = sorted(find_objects_by_key(key), key=lambda o: o.name.lower())

        layout.label(text=f"Found: {len(objs)}")
        col = layout.column(align=True)
        if not objs:
            col.label(text="No objects with that key.", icon='INFO')
        else:
            # 1) bucket objects by suffix
            buckets = defaultdict(list)
            for o in objs:
                value = o.get(key)
                buckets[_suffix_of(value)].append(o)

            # 2) deterministically order the suffixes (optional but nice)
            for suffix in sorted(buckets.keys()):
                items = buckets[suffix]

                # One box per suffix
                box = layout.box()
                box.label(text=f"Group: {suffix}", icon='LIGHT_DATA')

                # A column to stack per-object controls
                col = box.column(align=True)

                for o in items:
                    value = o.get(key) or "(unnamed)"
                    name_l = value.lower()

                    row = col.box()  # small sub-box per object for clarity
                    row.label(text=value, icon='LIGHT_DATA' if o.type == 'LIGHT' else 'EMPTY_DATA')

                    if o.type == 'LIGHT':
                        row.prop(o.data, "color", text="Color")
                        row.prop(o.data, "energy", text="Energy")
                        # Guard missing props in case render engine doesn't expose them
                        if hasattr(o.data, "exposure"):
                            row.prop(o.data, "exposure", text="Exposure")
                        if hasattr(o.data, "shadow_jitter_overblur"):
                            row.prop(o.data, "shadow_jitter_overblur", text="Shadow Jitter")

                    elif o.type == 'EMPTY':
                        # Aim/root helpers live here
                        if name_l.startswith("light_aim"):
                            # Z location only
                            row.prop(o, "location", index=2, text="Aim Z Location")

                        elif name_l.startswith("light_root"):
                            # Show rotation mode hint if not Euler
                            if o.rotation_mode not in {'XYZ', 'XZY', 'YXZ', 'YZX', 'ZXY', 'ZYX'}:
                                row.label(text=f"Rotation mode: {o.rotation_mode}", icon='INFO')
                            row.prop(o, "rotation_euler", index=2, text="Root Z Rotation")
                            row.prop(o, '["light_diameter"]', text="Light Diameter")

                        else:
                            row.label(text="Empty (not light_aim/root)")
                    else:
                        row.label(text="Not a Light object.", icon='ERROR')
                        row.label(text="Energy control is only available for lights.")
