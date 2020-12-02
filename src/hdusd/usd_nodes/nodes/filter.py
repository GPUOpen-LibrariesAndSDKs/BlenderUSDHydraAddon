import bpy
from .base_node import USDNode
from . import log


class FilterNode(USDNode):
    """Takes in USD and filters out matching path or names"""
    bl_idname = 'usd.FilterNode'
    bl_label = "Filter USD"

    filter_path: bpy.props.StringProperty(name='USD Path', default='*')

    def draw_buttons(self, context, layout):
        layout.prop(self, 'filter_path')

    def compute(self, **kwargs):
        stage = self.get_input_link('Input', **kwargs)
        # TODO: Implement: filter prims by some sort of regex
        return stage
