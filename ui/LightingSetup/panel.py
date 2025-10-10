import bpy

class LightingSetupUI:
    def __init__(self, layout, context):
        self.layout = layout
        self.context = context

    def draw(self):
        layout = self.layout
        s = self.context.scene
        props = s.lighting_setup

        row_func = layout.row(align=True)
        row_func.operator("bls.append_blend", text="Append Setup", icon="IMPORT")

