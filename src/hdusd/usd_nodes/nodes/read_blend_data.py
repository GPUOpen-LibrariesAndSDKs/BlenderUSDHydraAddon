import bpy

from .base_node import USDNode
from ...export import depsgraph as dp


class ReadBlendDataNode(USDNode):
    """Blender data to USD can export whole scene, one collection or object"""
    bl_idname = 'usd.ReadBlendDataNode'
    bl_label = "Read Blend Data"

    export_type: bpy.props.EnumProperty(
        name='Data to Read',
        items=(('SCENE', 'Scene', 'Read entire scene'),
            ('COLLECTION', 'Collection', 'Read collection'),
            ('OBJECT', 'Object', 'Read single object'),
        ),
        default='SCENE'
    )

    collection_to_export: bpy.props.PointerProperty(
        name='Collection', type=bpy.types.Collection
    )
    
    object_to_export: bpy.props.PointerProperty(
        name='Object', type=bpy.types.Object
    )

    def init(self, context):
        self.outputs.new(name="Output", type="NodeSocketShader")

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        col.use_property_split = False
        col.use_property_decorate = False

        flow = layout.grid_flow(row_major=True, even_columns=True, align=True)
        flow.prop(self, 'export_type')
        
        if self.export_type == 'COLLECTION':
            flow.prop(self, 'collection_to_export')
        elif self.export_type == 'OBJECT':
            flow.prop(self, 'object_to_export')

    def compute(self, **kwargs):
        stage = self.stage_cache.create_stage()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        dp.sync(stage, depsgraph, **kwargs)
        return stage
