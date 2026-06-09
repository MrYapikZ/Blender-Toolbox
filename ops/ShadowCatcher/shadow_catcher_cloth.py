import bpy
import os


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Create GOBOS Scene
def get_or_create_gobos():
    gobos = bpy.data.scenes.get("gobos")
    if gobos is None:
        gobos = bpy.data.scenes.new("gobos")
    return gobos

# Filename parser
def get_blend_parts():
    """Parse nama file .blend -> dict {blend_name, ep, sq, sh}."""
    blend_name = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
    if not blend_name:
        blend_name = "untitled"
    parts = blend_name.split('_')
    ep = next((p for p in parts if p.startswith('ep')), 'ep000')
    sq = next((p for p in parts if p.startswith('sq')), 'sq00')
    sh = next((p for p in parts if p.startswith('sh')), 'sh0000')
    return {"blend_name": blend_name, "ep": ep, "sq": sq, "sh": sh}

# Get base path
def get_output_base_path(ep):
    scenes = bpy.data.scenes["Scene"]
    path_char = scenes.node_tree.nodes["File Output Char"]
    if ep in path_char:
        base_path = path_char.split(ep)[0]
        return base_path.rstrip("\\/")
    
    return path_char

# Cloth cahce
def get_cloth_cache_path(obj):
    """Buat absolute cache path untuk cloth/softbody object."""
    info = get_blend_parts()
    ep, sq, sh = info['ep'], info['sq'], info['sh']
    base_path = get_output_base_path(ep)
    return f"{base_path}/{ep}/{ep}_{sq}/{ep}_{sq}_{sh}/cache/cloth/{obj.name}/"


# Softbody modifier cheker
def has_sim_modifier(obj):
    """Return True kalau object punya Cloth atau Softbody modifier."""
    for mod in obj.modifiers:
        if mod.type in ('CLOTH', 'SOFT_BODY'):
            return True
    return False


def fix_cloth_cache_path(obj):
    """
    Set cache path cloth/softbody ke absolute path yang konsisten.
    Return (fixed: bool, message: str)
    """
    for mod in obj.modifiers:
        if mod.type in ('CLOTH', 'SOFT_BODY'):
            cache = mod.point_cache
            new_path = get_cloth_cache_path(obj)
            old_path = cache.filepath
            cache.filepath = new_path
            if old_path != new_path:
                return (True, f"Cache path diupdate: {new_path}")
            return (False, f"Cache path sudah benar: {new_path}")
    return (False, "Tidak ada sim modifier")


# ---------------------------------------------------------------------------
# Operators
# ---------------------------------------------------------------------------

class SHADOWCATCHER_OT_add(bpy.types.Operator):
    """Buat linked copy objek ke scene GOBOS dan aktifkan Shadow Catcher di sana"""
    bl_idname = "sdc.add_to_shadow_catcher"
    bl_label = "Add Object to GOBOS Scene"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        gobos_scene = get_or_create_gobos()
        source_scene = context.scene

        if source_scene == gobos_scene:
            self.report({'WARNING'}, "Kamu sudah di scene GOBOS! Jalankan dari scene lain.")
            return {'CANCELLED'}

        selected_objects = list(context.selected_objects)
        if not selected_objects:
            self.report({'WARNING'}, "Tidak ada objek yang dipilih.")
            return {'CANCELLED'}

        added_count = 0
        skipped_count = 0
        cloth_warnings = []

        # Siapkan collection shadow_catcher di scene GOBOS
        col_sc = bpy.data.collections.get("shadow_catcher")
        if col_sc is None:
            col_sc = bpy.data.collections.new("shadow_catcher")
        if "shadow_catcher" not in gobos_scene.collection.children:
            gobos_scene.collection.children.link(col_sc)

        # Bangun index: source_name -> object yang sudah ada di GOBOS
        # Pakai custom property "gobos_source" sebagai fingerprint yang reliable,
        # tidak terpengaruh auto-rename Blender (.001, .002, dst)
        gobos_index = {}
        for o in gobos_scene.objects:
            src_name = o.get("gobos_source")
            if src_name:
                gobos_index[src_name] = o

        for obj in selected_objects:
            is_cloth_obj = has_sim_modifier(obj)

            # Cek apakah linked copy sudah ada di scene GOBOS via fingerprint
            existing = gobos_index.get(obj.name)

            # Fallback: object lama yang belum punya fingerprint — cek nama langsung
            if existing is None:
                existing = gobos_scene.objects.get(obj.name)
                if existing is not None:
                    # Tandai dengan fingerprint supaya run berikutnya langsung ketemu
                    existing["gobos_source"] = obj.name
                    gobos_index[obj.name] = existing

            if existing is not None:
                existing.is_shadow_catcher = True
                if existing.name not in col_sc.objects:
                    try:
                        col_sc.objects.link(existing)
                    except RuntimeError:
                        pass
                if is_cloth_obj:
                    self.make_local_and_bake_in_gobos(existing, gobos_scene, context)
                skipped_count += 1
                continue

            # Buat linked copy (Alt+D style: data sama, object baru)
            linked_copy = obj.copy()
            linked_copy.name = obj.name          # best-effort; Blender bisa rename
            linked_copy["gobos_source"] = obj.name  # fingerprint untuk cek duplikat
            linked_copy.is_shadow_catcher = True
            obj.is_shadow_catcher = False
            col_sc.objects.link(linked_copy)
            added_count += 1

            # Kalau cloth/softbody: make local di GOBOS lalu bake
            if is_cloth_obj:
                baked_ok = self.make_local_and_bake_in_gobos(linked_copy, gobos_scene, context)
                if not baked_ok:
                    cloth_warnings.append(obj.name)

        # Bawa extras (cam, lit, gobos) ke GOBOS
        self.link_extra_to_gobos(source_scene, gobos_scene)

        # Apply render settings
        self.apply_gobos_settings(gobos_scene, source_scene)

        # Report
        msg_parts = []
        if added_count > 0:
            msg_parts.append(f"{added_count} linked copy dibuat di GOBOS")
        if skipped_count > 0:
            msg_parts.append(f"{skipped_count} sudah ada di GOBOS")
        msg_parts.append("Shadow Catcher aktif ✓")
        if cloth_warnings:
            msg_parts.append(f"⚠ BELUM DI-BAKE: {', '.join(cloth_warnings)}")
        self.report({'INFO'} if not cloth_warnings else {'WARNING'}, " | ".join(msg_parts))
        return {'FINISHED'}

    # -----------------------------------------------------------------------
    # Helpers internal
    # -----------------------------------------------------------------------

    def get_or_create_lit_gobos(self, gobos_scene):
        col = bpy.data.collections.get("lit_gobos")
        if col is None:
            col = bpy.data.collections.new("lit_gobos")
        if "lit_gobos" not in gobos_scene.collection.children:
            gobos_scene.collection.children.link(col)
        return col

    def link_obj_to_lit_gobos(self, obj, lit_gobos_col, gobos_scene):
        if obj.name not in lit_gobos_col.objects:
            try:
                lit_gobos_col.objects.link(obj)
            except RuntimeError:
                pass

    def link_obj_to_gobos(self, obj, gobos_scene):
        if obj.name not in gobos_scene.objects:
            gobos_scene.collection.objects.link(obj)

    def link_collection_to_gobos(self, col, gobos_scene):
        if col.name not in gobos_scene.collection.children:
            try:
                gobos_scene.collection.children.link(col)
            except RuntimeError:
                pass

    def find_collections_by_keyword(self, scene, keyword):
        result = []
        def recurse(col):
            if keyword.lower() in col.name.lower():
                result.append(col)
            for child in col.children:
                recurse(child)
        recurse(scene.collection)
        return result

    def link_extra_to_gobos(self, source_scene, gobos_scene):
        lit_gobos_col = self.get_or_create_lit_gobos(gobos_scene)

        # 1. Collection 'cam'
        cam_col = None
        def find_cam(col):
            nonlocal cam_col
            if col.name.lower() == 'cam':
                cam_col = col
                return
            for child in col.children:
                find_cam(child)
        find_cam(source_scene.collection)

        if cam_col:
            self.link_collection_to_gobos(cam_col, gobos_scene)
        else:
            for obj in source_scene.objects:
                if obj.type == 'CAMERA':
                    self.link_obj_to_gobos(obj, gobos_scene)

        # 2. Collection 'lit_*' -> object 'key_*' -> lit_gobos
        lit_collections = self.find_collections_by_keyword(source_scene, 'lit_')
        for lit_col in lit_collections:
            def recurse_lit(col):
                for obj in col.objects:
                    if obj.name.lower().startswith('key_') or '_key_' in obj.name.lower():
                        self.link_obj_to_lit_gobos(obj, lit_gobos_col, gobos_scene)
                for child in col.children:
                    recurse_lit(child)
            recurse_lit(lit_col)

        # 3. Seluruh isi collection 'gobos' -> lit_gobos
        gobos_src_col = None
        def find_gobos_col(col):
            nonlocal gobos_src_col
            if col.name.lower() == 'gobos':
                gobos_src_col = col
                return
            for child in col.children:
                find_gobos_col(child)
        find_gobos_col(source_scene.collection)

        if gobos_src_col:
            def recurse_gobos(col):
                for obj in col.objects:
                    self.link_obj_to_lit_gobos(obj, lit_gobos_col, gobos_scene)
                for child in col.children:
                    recurse_gobos(child)
            recurse_gobos(gobos_src_col)

        # 4. Object 'gobos_*' -> lit_gobos
        for obj in source_scene.objects:
            if obj.name.lower().startswith('gobos_'):
                self.link_obj_to_lit_gobos(obj, lit_gobos_col, gobos_scene)

        # 5. Frame range
        gobos_scene.frame_start = source_scene.frame_start
        gobos_scene.frame_end = source_scene.frame_end

    def apply_gobos_settings(self, scene, source_scene):
        scene.render.engine = 'CYCLES'

        scene.cycles.device = 'GPU'
        scene.cycles.samples = 2
        scene.cycles.preview_samples = 2
        scene.cycles.adaptive_min_samples = 2
        scene.cycles.adaptive_threshold = 0.1
        scene.cycles.denoising_use_gpu = True

        scene.cycles.max_bounces = 4
        scene.cycles.diffuse_bounces = 0
        scene.cycles.glossy_bounces = 0
        scene.cycles.transmission_bounces = 0
        scene.cycles.volume_bounces = 0

        scene.render.use_simplify = True
        scene.render.simplify_subdivision = 2
        scene.render.simplify_subdivision_render = 2
        scene.render.resolution_x = 2560

        scene.cycles.texture_limit = '2048'
        scene.cycles.texture_limit_render = '2048'

        scene.render.image_settings.compression = 0
        scene.render.image_settings.color_depth = '16'
        scene.render.film_transparent = True
        scene.render.filepath = "/tmp/"
        scene.view_settings.view_transform = 'ARRI K1S1'

        info = get_blend_parts()
        blend_name = info['blend_name']
        ep, sq, sh = info['ep'], info['sq'], info['sh']
        base_path = get_output_base_path(ep)
        out_path = f"{base_path}/{ep}/{ep}_{sq}/{ep}_{sq}_{sh}/render/gobos/"
        file_slot_name = f"{blend_name}_gobos_####.png"

        scene.use_nodes = True
        node_tree = scene.node_tree
        node_tree.nodes.clear()

        rl_node = node_tree.nodes.new(type='CompositorNodeRLayers')
        rl_node.name = "Render Layers"
        rl_node.label = "Render Layers"
        rl_node.scene = scene
        rl_node.location = (-200, 300)

        file_out = node_tree.nodes.new(type='CompositorNodeOutputFile')
        file_out.name = "File Output Gobos"
        file_out.label = "File Output Gobos"
        file_out.location = (200, 300)
        file_out.base_path = out_path
        file_out.format.file_format = 'PNG'
        file_out.format.color_mode = 'RGBA'
        file_out.format.color_depth = '16'
        file_out.format.compression = 0
        file_out.file_slots[0].path = file_slot_name

        node_tree.links.new(rl_node.outputs['Image'], file_out.inputs[0])

    def make_local_and_bake_in_gobos(self, obj, gobos_scene, context):
        """
        Make local object cloth di GOBOS (tidak affect scene asal),
        set Disk Cache + absolute path, lalu bake.
        Return True kalau berhasil, False kalau gagal.
        """

        try:
            # --- Switch context ke GOBOS scene sementara ---
            orig_scene = context.window.scene
            orig_view_layer = context.window.view_layer  # <-- simpan view layer asal
            context.window.scene = gobos_scene

            # --- Pastikan object ini ada di GOBOS dan ter-select ---
            # Deselect semua dulu
            for o in gobos_scene.objects:
                o.select_set(False)

            # Set active + select object cloth di GOBOS
            gobos_scene.view_layers[0].objects.active = obj
            obj.select_set(True)

            # --- Make Local: hanya object + data (tidak affect source scene) ---
            # Ini membuat object + mesh data menjadi local di file ini
            # tapi HANYA untuk object ini di GOBOS — source scene tidak tersentuh
            bpy.ops.object.make_local(type='SELECT_OBJECT')

            # --- Set Disk Cache & path di modifier ---
            for mod in obj.modifiers:
                if mod.type in ('CLOTH', 'SOFT_BODY'):
                    cache = mod.point_cache
                    cache.use_disk_cache = True
                    cache.filepath = get_cloth_cache_path(obj)
                    cache.use_library_path = False
                    cache.frame_start = 90
                    break

            # --- Bake ---
            bpy.ops.ptcache.bake_all(bake=True)

            # --- Kembalikan ke scene asal + view layer asal ---
            context.window.scene = orig_scene
            context.window.view_layer = orig_view_layer  # <-- restore view layer

            return True

        except Exception as e:
            # Kembalikan ke scene asal walau error
            try:
                context.window.scene = orig_scene
                context.window.view_layer = orig_view_layer  # <-- restore view layer
            except Exception:
                pass
            self.report({'WARNING'}, f"Gagal bake cloth {obj.name}: {str(e)}")
            return False


class SHADOWCATCHER_OT_fix_cloth(bpy.types.Operator):
    """Fix cache path cloth/softbody ke absolute path pipeline"""
    bl_idname = "sdc.fix_cloth_cache"
    bl_label = "Fix Cloth Cache Path"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected = list(context.selected_objects)
        if not selected:
            self.report({'WARNING'}, "Tidak ada objek yang dipilih.")
            return {'CANCELLED'}

        fixed = []
        skipped = []
        for obj in selected:
            if has_sim_modifier(obj):
                changed, msg = fix_cloth_cache_path(obj)
                if changed:
                    fixed.append(obj.name)
                else:
                    skipped.append(obj.name)

        msg_parts = []
        if fixed:
            msg_parts.append(f"Cache path difix: {', '.join(fixed)}")
        if skipped:
            msg_parts.append(f"Sudah benar: {', '.join(skipped)}")
        if not fixed and not skipped:
            msg_parts.append("Tidak ada object dengan cloth/softbody modifier")

        self.report({'INFO'}, " | ".join(msg_parts))
        return {'FINISHED'}


class SHADOWCATCHER_OT_remove(bpy.types.Operator):
    """Hapus linked copy Shadow Catcher dari scene GOBOS"""
    bl_idname = "object.remove_shadow_catcher"
    bl_label = "Remove from Shadow Catcher"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        gobos_scene = bpy.data.scenes.get("GOBOS")
        if gobos_scene is None:
            self.report({'WARNING'}, "Scene GOBOS tidak ditemukan.")
            return {'CANCELLED'}

        selected_objects = list(context.selected_objects)
        if not selected_objects:
            self.report({'WARNING'}, "Tidak ada objek yang dipilih.")
            return {'CANCELLED'}

        count = 0
        for obj in selected_objects:
            copy_obj = gobos_scene.objects.get(obj.name)
            if copy_obj and copy_obj.data == obj.data:
                bpy.data.objects.remove(copy_obj, do_unlink=True)
                count += 1

        self.report({'INFO'}, f"{count} shadow catcher copy dihapus dari GOBOS.")
        return {'FINISHED'}


class SHADOWCATCHER_OT_go_to_gobos(bpy.types.Operator):
    """Switch active scene to GOBOS"""
    bl_idname = "sdc.go_to_gobos_scene"
    bl_label = "Go to GOBOS Scene"

    def execute(self, context):
        gobos_scene = get_or_create_gobos()
        context.window.scene = gobos_scene
        return {'FINISHED'}


def register():
    bpy.utils.register_class(SHADOWCATCHER_OT_add)
    bpy.utils.register_class(SHADOWCATCHER_OT_fix_cloth)
    bpy.utils.register_class(SHADOWCATCHER_OT_remove)


def unregister():
    bpy.utils.unregister_class(SHADOWCATCHER_OT_add)
    bpy.utils.unregister_class(SHADOWCATCHER_OT_fix_cloth)
    bpy.utils.unregister_class(SHADOWCATCHER_OT_remove)
