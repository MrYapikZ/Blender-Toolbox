import bpy


# ------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------
def find_objects_by_key(key=""):
    override_objects = [obj for obj in bpy.data.objects if obj.override_library]
    return [o for o in override_objects if o.get(key)]


def get_compositor_tree(scene: bpy.types.Scene):
    """Return the scene's compositor node tree, or None safely."""
    if not scene:
        return None
    # In Blender 3.x/4.x, the compositor lives on the scene's node_tree
    tree = getattr(scene, "node_tree", None)
    return tree if tree and isinstance(tree, bpy.types.NodeTree) else None


def find_occlusion_node(scene: bpy.types.Scene):
    """Return the node named 'Occlusion_Thickness' if it exists."""
    tree = get_compositor_tree(scene)
    if not tree:
        return None
    return tree.nodes.get("Occlusion_Thickness")


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

        row_func = layout.row(align=True)
        row_func.operator("blp.make_override_lights_local", text="Override Light", icon="LIBRARY_DATA_OVERRIDE")
        # make func to detect bpy.data.scenes["Scene"].node_tree.nodes["Occlusion_Thickness"] exists or not

        row = layout.row(align=True)
        row.operator("view3d.refresh_custom_prop_list", text="", icon="FILE_REFRESH")
        eevee = self.context.scene.eevee
        row.prop(eevee, "gtao_distance", text="AO Distance")

        occ_box = layout.box()

        node = find_occlusion_node(s)
        if not node:
            occ_box.label(text="Compositor node 'Occlusion_Thickness' not found.", icon='ERROR')
        else:
            sock = get_thickness_socket(node)
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
                    row.prop(sock, "default_value", text="AO Thickness")

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
                else:
                    box.label(text="Not a Light object.", icon='ERROR')
                    box.label(text="Energy control is only available for lights.")
