import bpy
from .base_node import USDNode

from . import log


class WriteFileNode(USDNode):
    """Writes stream out to USD file"""
    bl_idname = 'usd.WriteFileNode'
    bl_label = "Write USD File"

    file_path: bpy.props.StringProperty(name="USD File", subtype='FILE_PATH')

    def init(self, context):
        self.inputs.new(name="Input", type="NodeSocketShader")
        self.outputs.new(name="Output", type="NodeSocketShader")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'file_path')

    def compute(self, **kwargs):
        if not self.file_path:
            return None

        stage = self.get_input_link('Input', **kwargs)
        if stage:
            file_path = bpy.path.abspath(self.file_path)
            stage.Export(file_path)

        return stage
