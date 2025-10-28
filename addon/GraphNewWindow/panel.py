import bpy
import rna_keymap_ui

addon_keymaps = []

class GraphNewWindowPrefUI:
    def __init__(self, layout, context):
        self.layout = layout
        self.context = context

    def draw(self):
        layout = self.layout

        layout.label(text="Graph New Window:", icon='KEYTYPE_JITTER_VEC')
        kc = bpy.context.window_manager.keyconfigs.addon
        for km, kmi in addon_keymaps:
            km = km.active()
            layout.context_pointer_set("keymap", km)
            rna_keymap_ui.draw_kmi([], kc, km, kmi, layout, 0)

def register():
    kc = bpy.context.window_manager.keyconfigs.addon
    km = kc.keymaps.new(name='Window', space_type='EMPTY', region_type='WINDOW')
    kmi = km.keymap_items.new('gnw.graph_new_window', 'F6', 'PRESS', ctrl=False)
    kmi.active = True
    addon_keymaps.append((km, kmi))

def unregister():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    km = kc.keymaps['Window']

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
        wm.keyconfigs.addon.keymaps.remove(km)
    addon_keymaps.clear()