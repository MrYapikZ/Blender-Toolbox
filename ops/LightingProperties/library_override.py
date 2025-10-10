import bpy


# ------------------------------------------------------------------------
# Make Override Lights Local Operator
# ------------------------------------------------------------------------
class OBJECT_OT_make_override_lights_local(bpy.types.Operator):
    """Make datablocks of library-override LIGHT objects local, then optionally purge unused linked lights"""
    bl_idname = "blp.make_override_lights_local"
    bl_label = "Make Override Lights Local"
    bl_options = {'REGISTER', 'UNDO'}

    @staticmethod
    def is_override_id(id_):
        # Works in Blender 3.x/4.x: local override IDs have non-None override_library
        return getattr(id_, "override_library", None) is not None

    @classmethod
    def poll(cls, context):
        # Always allowed; operator just scans data
        return True

    def execute(self, context):
        view_layer = context.view_layer
        s = context.scene
        props = s.lighting_props
        key = props.key

        # Collect target objects
        if props.only_selected:
            candidates = [o for o in context.selected_objects if o.type == 'LIGHT']
        else:
            candidates = [o for o in bpy.data.objects if o.type == 'LIGHT']

        # Filter to library override objects
        override_lights = [o for o in candidates if self.is_override_id(o)]

        # Select & set active for user feedback (non-destructive)
        for o in bpy.data.objects:
            o.select_set(False)
        for o in override_lights:
            o.select_set(True)
        if override_lights:
            view_layer.objects.active = override_lights[0]

        made_local_count = 0
        already_local_count = 0
        skipped_none_count = 0

        # Make Light datablocks local by copying if they come from a library
        for obj in override_lights:
            L = obj.data
            if L is None:
                skipped_none_count += 1
                continue
            if getattr(L, "library", None) is not None:
                obj.data = L.copy()
                obj.data.name = f"{key}_{obj.get(key)}_Light"
                made_local_count += 1
            else:
                already_local_count += 1

        purged_count = 0
        if props.purge_unreferenced:
            # Remove linked Light datablocks with zero users
            # Use list(...) to avoid modifying while iterating
            for L in list(bpy.data.lights):
                if getattr(L, "library", None) is not None and L.users == 0:
                    bpy.data.lights.remove(L)
                    purged_count += 1

        self.report(
            {'INFO'},
            (f"Processed {len(override_lights)} override LIGHT objects | "
             f"Made local: {made_local_count} | Already local: {already_local_count} | "
             f"Null data: {skipped_none_count} | Purged linked lights: {purged_count}")
        )
        return {'FINISHED'}


# ------------------------------------------------------------------------
# Register
# ------------------------------------------------------------------------
def register():
    bpy.utils.register_class(OBJECT_OT_make_override_lights_local)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_make_override_lights_local)