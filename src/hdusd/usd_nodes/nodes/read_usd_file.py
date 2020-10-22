import os

import bpy
from .base_node import USDNode
from . import log


class ReadUsdFileNode(USDNode):
    ''' read USD file '''
    bl_idname = 'usd.ReadUsdFileNode'
    bl_label = "Read USD File"

    filename: bpy.props.StringProperty(name="USD File", subtype='FILE_PATH')

    def init(self, context):
        self.outputs.new(name="Output", type="NodeSocketShader")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'filename')

    def compute(self, **kwargs):
        from pxr import Usd

        if not self.filename:
            log.warn("USD file name not set, skipping node", self)
            return None

        file_path = bpy.path.abspath(self.filename)
        if not os.path.isfile(file_path):
            log.warn("Couldn't find USD file", self.filename, self)
            return None

        stage = Usd.Stage.Open(file_path)
        return stage
