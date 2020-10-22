import numpy as np
import time

import bpy
from .base_node import USDNode
from . import log


class HydraRenderNode(USDNode):
    """Render to Hydra"""
    
    bl_idname = 'usd.HydraRenderNode'
    bl_label = "Render USD via Hydra"

    render_type: bpy.props.EnumProperty(
        name='Type',
        items=(('FINAL', 'Final', 'Final Render'),
            ('VIEWPORT', 'Viewport', 'Viewport Render'),
            ('BOTH', 'Both', 'All Renders'),
        ),
        default='BOTH'
    )
    
    def init(self, context):
        self.inputs.new(name="Input", type="NodeSocketShader")
    
    def draw_buttons(self, context, layout):
        layout.prop(self, 'render_type')


    def compute(self, **kwargs):
        stage = self.get_input_link('Input', **kwargs)
        return stage
