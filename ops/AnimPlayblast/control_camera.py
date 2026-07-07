import bpy


OVERLAY_PRESET: dict = {
    # --- Guides ---
    "show_grid":               True,
    "show_floor":              False,
    "show_axis_x":             False,
    "show_axis_y":             False,
    "show_axis_z":             False,
    "grid_scale":              1.0,
    "grid_subdivisions":       10,
    "show_text_info":          False,
    "show_cursor":             False,
    "show_stats":              False,
    "show_annotation":         False,
    "show_camera_guides":      False,

    # --- Objects ---
    "show_extras":             False,
    "show_bones":              False,
    "show_motion_paths":       False,
    "show_relationship_lines": False,
    "show_object_origins":     False,
    "show_outline_selected":   False,
    "show_object_origins_all": False,

    # --- Geometry ---
    "show_wireframes":         False,
    "wireframe_opacity":       1.0,
    "show_face_orientation":   False,

    # --- Viewer Node ---
    "viewer_node_border_opacity": 1.0,

    # --- Motion Tracking ---
    "show_motion_tracking":    False,
}

OVERLAY_PRESET_DEFAULT: dict = {
    # --- Guides ---
    "show_grid":               True,
    "show_floor":              True,
    "show_axis_x":             True,
    "show_axis_y":             True,
    "show_axis_z":             False,
    "grid_scale":              1.0,
    "grid_subdivisions":       10,
    "show_text_info":          True,
    "show_cursor":             True,
    "show_stats":              False,
    "show_annotation":         True,
    "show_camera_guides":      True,

    # --- Objects ---
    "show_extras":             True,
    "show_bones":              True,
    "show_motion_paths":       True,
    "show_relationship_lines": True,
    "show_object_origins":     True,
    "show_outline_selected":   True,
    "show_object_origins_all": False,

    # --- Geometry ---
    "show_wireframes":         False,
    "wireframe_opacity":       1.0,
    "show_face_orientation":   False,

    # --- Viewer Node ---
    "viewer_node_border_opacity": 1.0,

    # --- Motion Tracking ---
    "show_motion_tracking":    False,
}
# ------------------------------------------------------------------------
# Helper
# ------------------------------------------------------------------------

def apply_overlay(overlay, preset):
    for key, value in preset.items():
        if hasattr(overlay, key) and value is not None:
            try:
                setattr(overlay, key, value)
            except (AttributeError, TypeError) as e:
                print(f"[BJL] Gagal set '{key}': {e}")


# ------------------------------------------------------------------------
# Control Camera - Operator
# ------------------------------------------------------------------------

class APB_OT_ViewCamera(bpy.types.Operator):
    """Switch to camera view"""
    bl_idname = "apb.view_camera_operator"
    bl_label = "View Camera"

    def execute(self, context):
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        region_3d = space.region_3d
                        overlay = space.overlay
                        overlay.show_overlays = True
                        apply_overlay(overlay, OVERLAY_PRESET)
                        region_3d.view_perspective = 'CAMERA'
                        self.report({'INFO'}, "Switched to Camera View")
        return {'FINISHED'}

class APB_OT_ViewCameraDefault(bpy.types.Operator):
    """Switch to camera view default"""
    bl_idname = "apb.view_camera_operator_default"
    bl_label = "View Camera"

    def execute(self, context):
        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        region_3d = space.region_3d
                        overlay = space.overlay
                        overlay.show_overlays = True
                        apply_overlay(overlay, OVERLAY_PRESET_DEFAULT)
                        region_3d.view_perspective = 'CAMERA'
                        self.report({'INFO'}, "Switched to Camera View")
        return {'FINISHED'}

class APB_OT_return_solid(bpy.types.Operator):
    """Return to previous view"""
    bl_idname = "apb.return_solid"
    bl_label = "Return View"

    def execute(self, context):
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        # space.shading.type = 'MATERIAL'
                        space.shading.type = 'SOLID'
                        space.shading.color_type = 'MATERIAL'
                        break
        return {'FINISHED'}


def register():
    bpy.utils.register_class(APB_OT_ViewCamera)
    bpy.utils.register_class(APB_OT_return_solid)
    bpy.utils.register_class(APB_OT_ViewCameraDefault)


def unregister():
    bpy.utils.unregister_class(APB_OT_ViewCamera)
    bpy.utils.unregister_class(APB_OT_return_solid)
    bpy.utils.unregister_class(APB_OT_ViewCameraDefault)
