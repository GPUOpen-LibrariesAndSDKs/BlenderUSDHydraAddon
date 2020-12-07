import bpy
from .base_node import USDNode
from . import log


class USDToBlenderNode(USDNode):
    """Import USD to blender"""
    
    bl_idname = 'usd.USDToBlenderNode'
    bl_label = "Insert USD to Blender"

    output_name = ""

    write_type: bpy.props.EnumProperty( 
        name='Type',
        items=(('REFERENCE', 'Reference', "Load Data as Reference"),
               ('COPY', 'Copy', "Copy data into Blender")), 
        default='REFERENCE')
    object_pointer: bpy.props.PointerProperty(name='Object', type=bpy.types.Object)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'write_type')
        layout.prop(self, 'object_pointer')

    def compute(self, **kwargs):
        log("Reading Blend Data")
        # TODO: Implement
        return None
