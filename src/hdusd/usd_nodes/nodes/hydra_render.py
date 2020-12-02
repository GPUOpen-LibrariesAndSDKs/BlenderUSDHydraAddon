import bpy
from .base_node import USDNode
from . import log


class HydraRenderNode(USDNode):
    """Render to Hydra"""
    
    bl_idname = 'usd.HydraRenderNode'
    bl_label = "Render USD via Hydra"

    output_name = ""

    render_type: bpy.props.EnumProperty(
        name='Type',
        items=(('FINAL', 'Final', 'Final Render'),
            ('VIEWPORT', 'Viewport', 'Viewport Render'),
            ('BOTH', 'Both', 'All Renders'),
        ),
        default='BOTH'
    )

    def compute(self, **kwargs):
        stage = self.get_input_link('Input', **kwargs)
        return stage
