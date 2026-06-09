import bpy

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def has_sim_modifier(obj):
    """Return True kalau object punya Cloth atau Softbody modifier."""
    for mod in obj.modifiers:
        if mod.type in ('CLOTH', 'SOFT_BODY'):
            return True
    return False


def get_sim_status(obj):
    """
    Return tuple (modifier, is_baked, cache_path) untuk object dengan sim.
    Return None kalau tidak ada sim modifier.
    """
    for mod in obj.modifiers:
        if mod.type == 'CLOTH':
            cache = mod.point_cache
            is_baked = cache.is_baked
            cache_path = bpy.path.abspath(cache.filepath) if cache.filepath else ""
            return (mod, is_baked, cache_path)
        elif mod.type == 'SOFT_BODY':
            cache = mod.point_cache
            is_baked = cache.is_baked
            cache_path = bpy.path.abspath(cache.filepath) if cache.filepath else ""
            return (mod, is_baked, cache_path)
    return None


# ---------------------------------------------------------------------------
# Panel
# ---------------------------------------------------------------------------

class ShadowCatcherUI:
    def __init__(self, layout, context):
        self.layout = layout
        self.context = context

    def draw(self):
        layout = self.layout
        scene = self.context.scene
        gobos_scene = bpy.data.scenes.get("GOBOS")

        # --- Info box ---
        box = layout.box()
        col = box.column(align=True)
        col.label(text=f"Scene Aktif: {scene.name}", icon='SCENE_DATA')
        if gobos_scene:
            col.label(text="Scene GOBOS: ✓ Ditemukan", icon='CHECKMARK')
        else:
            col.label(text="Scene GOBOS: akan dibuat otomatis", icon='INFO')

        selected = self.context.selected_objects
        if selected:
            col.label(text=f"Dipilih: {len(selected)} objek", icon='OBJECT_DATA')
        else:
            col.label(text="Pilih objek dulu", icon='INFO')

        # --- Cloth sim status untuk selected objects ---
        sim_objects = [obj for obj in selected if has_sim_modifier(obj)]
        if sim_objects:
            layout.separator()
            box_cloth = layout.box()
            box_cloth.label(text="Cloth / Softbody Sim:", icon='MOD_CLOTH')
            for obj in sim_objects:
                sim_info = get_sim_status(obj)
                row = box_cloth.row(align=True)
                if sim_info:
                    mod, is_baked, cache_path = sim_info
                    if is_baked:
                        row.label(text=f"✓ {obj.name}", icon='CHECKMARK')
                    else:
                        row.alert = True
                        row.label(text=f"⚠ {obj.name}  — BELUM DI-BAKE!", icon='ERROR')
                else:
                    row.label(text=obj.name, icon='OBJECT_DATA')

            # Tombol fix cache path
            layout.operator(
                "sdc.fix_cloth_cache",
                text="Fix Cloth Cache Path",
                icon='FILE_FOLDER'
            )

        layout.separator()

        # --- Tombol utama ---
        row = layout.row()
        row.scale_y = 1.8
        row.operator(
            "sdc.add_to_shadow_catcher",
            text="➕ Add Object to GOBOS Scene",
            icon='SHADING_RENDERED'
        )

        # # --- List shadow catchers di GOBOS ---
        # if gobos_scene:
        #     layout.separator()
        #     box2 = layout.box()
        #     box2.label(text="Shadow Catchers di GOBOS:", icon='LIGHT')
        #     sc_objects = [o for o in gobos_scene.objects if o.is_shadow_catcher]
        #     if sc_objects:
        #         for o in sc_objects[:8]:
        #             row = box2.row()
        #             # Highlight kalau object source-nya punya cloth yang belum di-bake
        #             src_obj = scene.objects.get(o.name)
        #             if src_obj and has_sim_modifier(src_obj):
        #                 sim_info = get_sim_status(src_obj)
        #                 if sim_info and not sim_info[1]:  # not is_baked
        #                     row.alert = True
        #                     row.label(text=f"⚠ {o.name}", icon='ERROR')
        #                     continue
        #             row.label(text=o.name, icon='OBJECT_DATA')
        #         if len(sc_objects) > 8:
        #             box2.label(text=f"... dan {len(sc_objects)-8} lainnya")
        #     else:
        #         box2.label(text="(kosong)", icon='INFO')