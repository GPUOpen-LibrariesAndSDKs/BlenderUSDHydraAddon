import bpy
from .base_node import USDNode


class WriteFileNode(USDNode):
    """Writes stream out to USD file"""
    bl_idname = 'usd.WriteFileNode'
    bl_label = "Write USD File"

    file_path: bpy.props.StringProperty(name="USD File", subtype='FILE_PATH')

    def draw_buttons(self, context, layout):
        layout.prop(self, 'file_path')

    def compute(self, **kwargs):
        stage = self.get_input_link('Input', **kwargs)

        if stage and self.file_path:
            file_path = bpy.path.abspath(self.file_path)
            stage.Export(file_path)

        return stage
