import bpy
from pathlib import Path

from ...utils.file_manager import FileManager


# ------------------------------------------------------------------------
# Add Safe Area - Operator
# ------------------------------------------------------------------------
class APB_OT_AddSafeArea(bpy.types.Operator):
    bl_idname = "apb.add_safe_area"
    bl_label = "Add Safe Area"
    bl_description = "Add a safe area overlay to the active camera"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        cam = context.scene.camera
        if cam is None:
            cams = [obj for obj in bpy.data.objects if obj.type == 'CAMERA']
            cam = cams[0] if cams else None

        if cam and cam.type == 'CAMERA':
            cam.data.show_background_images = True

            if not cam.data.background_images:
                cam.data.background_images.new()

            bg = cam.data.background_images[0]

            raw_path = context.scene.exconfig.safe_area_path
            img_path = FileManager.get_filepath(raw_path)
            img_name = Path(img_path).name
            if not bpy.data.images.get(img_name):
                bg.image = bpy.data.images.load(img_path)
            else:
                bg.image = bpy.data.images[img_name]

            cs = bg.image.colorspace_settings
            color_spaces = {e.identifier for e in cs.bl_rna.properties['name'].enum_items}

            if 'Linear ACES - AP0' in color_spaces:
                cs.name = 'Linear ACES - AP0'
            elif 'Linear CIE-XYZ D65' in color_spaces:
                cs.name = 'Linear CIE-XYZ D65'
            else:
                cs.name = 'sRGB'
            bg.display_depth = 'FRONT'
            bg.scale = 1.0
            bg.alpha = 1.0

            img = bpy.data.images[img_name]
            img.pack()

            self.report({'INFO'}, f"Safe area added to camera '{cam.name}'")
        else:
            self.report({'WARNING'}, "No camera found")

        return {'FINISHED'}


def register():
    bpy.utils.register_class(APB_OT_AddSafeArea)


def unregister():
    bpy.utils.unregister_class(APB_OT_AddSafeArea)
