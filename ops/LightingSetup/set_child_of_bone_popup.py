import bpy

# Global "return value"
CUSTOM_BONE_NAME = None


def _poll_armature(self, obj):
    return (obj is not None) and (obj.type == 'ARMATURE')


def _enum_bones(self, context):
    rig = self.rig_obj
    if rig and rig.type == 'ARMATURE' and rig.pose:
        return [(pb.name, pb.name, "") for pb in rig.pose.bones]
    return [("", "<no bones>", "")]


class LIGHTINGSETUP_OT_set_child_of_bone_popup(bpy.types.Operator):
    """Pick a rig and a bone; stores result in CUSTOM_BONE_NAME"""
    bl_idname = "bls.set_child_of_bone_popup"
    bl_label = "Select Bone"
    bl_options = {'REGISTER', 'UNDO'}

    # Let user pick a rig (searchable field that filters to Armatures)
    rig_obj: bpy.props.PointerProperty(
        name="Rig",
        type=bpy.types.Object,
        poll=_poll_armature
    )

    # Dropdown populated from rig.pose.bones
    bone_name: bpy.props.EnumProperty(
        name="Bone",
        items=_enum_bones,
        description="Choose a pose bone from the selected rig",
        options={'ENUM_FLAG'}
    )

    def invoke(self, context, event):
        # Auto-pick a rig if still empty
        if not self.rig_obj:
            sel = context.selected_objects or []
            arm = next((o for o in sel if o.type == 'ARMATURE'), None)
            if not arm:
                arm = next((o for o in context.scene.objects if o.type == 'ARMATURE'), None)
            self.rig_obj = arm

        # Preselect common bones
        rig = self.rig_obj
        if rig and rig.pose:
            if "c_traj" in rig.pose.bones:
                self.bone_name = "c_traj"
            elif "body" in rig.pose.bones:
                self.bone_name = "body"

        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        col = self.layout.column(align=True)
        col.prop(self, "rig_obj")
        col.prop(self, "bone_name")

    def execute(self, context):
        global CUSTOM_BONE_NAME
        rig = self.rig_obj

        if not (rig and rig.type == 'ARMATURE'):
            self.report({'ERROR'}, "Pick a valid Armature rig.")
            return {'CANCELLED'}
        if not self.bone_name:
            self.report({'ERROR'}, "Pick a bone.")
            return {'CANCELLED'}

        CUSTOM_BONE_NAME = self.bone_name
        self.report({'INFO'}, f"Selected bone: {CUSTOM_BONE_NAME}")
        return {'FINISHED'}


def register():
    bpy.utils.register_class(LIGHTINGSETUP_OT_set_child_of_bone_popup)


def unregister():
    bpy.utils.unregister_class(LIGHTINGSETUP_OT_set_child_of_bone_popup)
