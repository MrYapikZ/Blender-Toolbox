import bpy

# ============================================================
# KONFIGURASI
# ============================================================
# NAMA_CHAR TIDAK perlu diisi manual lagi - diambil otomatis dari
# nama object armature yang sedang active/selected saat operator dijalankan.

# (bone posisi bola, template nama mesh, nama constraint, bone target constraint, scale)
BB_MAP = [
    ("c_head.x",         "bb_head_{}",  "Child_Of_bb_head",  "head.x",     0.09),
    ("c_spine_03.x",     "bb_spine_{}", "Child_Of_bb_spine", "spine_03.x", 0.15),
    ("c_root_master.x",  "bb_root_{}",  "Child_Of_bb_root",  "root.x",     0.15),
]

PARENT_COLLECTION_NAME = "bb_guide"
MATERIAL_NAME = "bb_material"  # satu material, dipakai bersama oleh semua karakter

DIFFUSE_COLOR = (0.007065220735967159, 0.8014093637466431, 0.0, 1.0)
METALLIC = 0.82
ROUGHNESS = 1.0
SPHERE_SEGMENTS = 16
SPHERE_RINGS = 8


def get_or_create_collection(name, parent_collection=None):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        if parent_collection is not None:
            parent_collection.children.link(col)
        else:
            bpy.context.scene.collection.children.link(col)
    return col


def get_or_create_material(name):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    mat.diffuse_color = DIFFUSE_COLOR
    mat.metallic = METALLIC
    mat.roughness = ROUGHNESS
    return mat


def create_bounding_balls(armature_obj, report=None):
    """Core logic. armature_obj must be a valid ARMATURE object.
    NAMA_CHAR is derived from armature_obj.name automatically."""

    nama_char = armature_obj.name

    armature_data = armature_obj.data
    original_pose_position = armature_data.pose_position

    collection_name = f"bb_guide_{nama_char}"

    parent_collection = get_or_create_collection(PARENT_COLLECTION_NAME)
    collection = get_or_create_collection(collection_name, parent_collection=parent_collection)
    material = get_or_create_material(MATERIAL_NAME)

    created = []

    try:
        # masuk rest pose dulu, supaya posisi bone = posisi netral rig
        armature_data.pose_position = 'REST'
        bpy.context.view_layer.update()

        for pos_bone_name, mesh_name_tmpl, constraint_name, target_bone_name, scale in BB_MAP:
            pose_bone = armature_obj.pose.bones.get(pos_bone_name)
            if pose_bone is None:
                print(f"[SKIP] Bone posisi '{pos_bone_name}' tidak ditemukan, dilewati.")
                continue

            target_pose_bone = armature_obj.pose.bones.get(target_bone_name)
            if target_pose_bone is None:
                print(f"[WARNING] Target bone '{target_bone_name}' untuk constraint "
                      f"'{constraint_name}' tidak ditemukan di armature.")

            mesh_name = mesh_name_tmpl.format(nama_char)

            # origin bone (head), world space, saat rest pose
            world_pos = armature_obj.matrix_world @ pose_bone.head

            bpy.ops.mesh.primitive_uv_sphere_add(
                segments=SPHERE_SEGMENTS,
                ring_count=SPHERE_RINGS,
                radius=1.0,
                location=world_pos,
            )
            sphere_obj = bpy.context.active_object
            sphere_obj.name = mesh_name
            sphere_obj.data.name = mesh_name
            sphere_obj.scale = (scale, scale, scale)

            # pindahkan ke collection bb_guide
            for col in list(sphere_obj.users_collection):
                col.objects.unlink(sphere_obj)
            collection.objects.link(sphere_obj)

            # assign material
            if sphere_obj.data.materials:
                sphere_obj.data.materials[0] = material
            else:
                sphere_obj.data.materials.append(material)

            # child of constraint
            con = sphere_obj.constraints.new(type='CHILD_OF')
            con.name = constraint_name
            con.target = armature_obj
            con.subtarget = target_bone_name

            if target_pose_bone is not None:
                # setara "Set Inverse": bola tetap di posisi origin pos_bone_name,
                # tapi ikut bergerak relatif terhadap target_bone_name
                target_matrix_world = armature_obj.matrix_world @ target_pose_bone.matrix
                con.inverse_matrix = target_matrix_world.inverted()

            created.append(sphere_obj)

    finally:
        # apapun yang terjadi, armature harus balik ke pose_position semula
        armature_data.pose_position = original_pose_position

    print(f"Selesai. {len(created)} bounding ball dibuat untuk '{nama_char}': "
          f"{[o.name for o in created]}")

    return created, nama_char
 
 
# ============================================================
# OPERATOR
# ============================================================
class ANMMISC_OT_create_bb_guide(bpy.types.Operator):
    """Buat bounding-ball guide mesh untuk armature yang sedang active/selected"""
    bl_idname = "anmmsc.create_bb_guide"
    bl_label = "Create Bounding Ball Guide"
    bl_options = {'REGISTER', 'UNDO'}
 
    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'ARMATURE'
 
    def execute(self, context):
        armature_obj = context.active_object
 
        if armature_obj is None or armature_obj.type != 'ARMATURE':
            self.report({'ERROR'}, "Select armature dulu sebelum menjalankan operator ini.")
            return {'CANCELLED'}
 
        created, nama_char = create_bounding_balls(armature_obj, report=self.report)
 
        self.report({'INFO'}, f"{len(created)} bounding ball dibuat untuk '{nama_char}'.")
        return {'FINISHED'}
    

def register():
    bpy.utils.register_class(ANMMISC_OT_create_bb_guide)


def unregister():
    bpy.utils.unregister_class(ANMMISC_OT_create_bb_guide)
