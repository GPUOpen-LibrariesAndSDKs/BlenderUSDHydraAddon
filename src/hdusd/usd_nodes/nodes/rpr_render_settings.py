import bpy
from .base_node import USDNode
from . import log


class RprRenderSettingsNode(USDNode):
    """RPR Render Settings"""
    bl_idname = 'usd.RprRenderSettingsNode'
    bl_label = "RPR Render Settings"

    render_mode: bpy.props.EnumProperty( 
        name='Render Mode',
        items=(('LOW', 'Low', "Raster only"),
               ('MEDIUM', 'Medium', "Rasterized with biased GI"),
               ('HIGH', 'High', "Vulkan ray tracer"),
               ('FULL', 'Full', 'OpenCL Path Tracing')), 
        default='FULL')
    max_samples: bpy.props.IntProperty(name='Max Samples', min=1, default=256)
    adaptive_threshold: bpy.props.FloatProperty(name='Noise Threshold', min=0, max=1.0, default=0.005)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'render_mode')
        layout.prop(self, 'max_samples')
        layout.prop(self, 'adaptive_threshold')

    def compute(self, **kwargs):
        stage = self.get_input_link('Input', **kwargs)
        # TODO: Implement
        return stage
