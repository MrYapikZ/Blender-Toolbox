import bpy

class AnimMiscUI:
    def __init__(self, layout, context):
        self.layout = layout
        self.context = context

    def draw(self):
        layout = self.layout
        s = self.context.scene

        column = layout.column(align=True)
        column.operator("anmmsc.create_bb_guide", text="Add Sphere", icon='SPHERE')