# **********************************************************************
# Copyright 2020 Advanced Micro Devices, Inc
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ********************************************************************
import bpy

from .base_node import USDNode
from ...export import depsgraph as dp


class ReadBlendDataNode(USDNode):
    """Blender data to USD can export whole scene, one collection or object"""
    bl_idname = 'usd.ReadBlendDataNode'
    bl_label = "Read Blend Data"

    input_names = ()

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
        stage = self.cached_stage.create()
        depsgraph = bpy.context.evaluated_depsgraph_get()
        dp.sync(stage, depsgraph, **kwargs)
        return stage

    def depsgraph_update(self, depsgraph):
        nodetree = self.id_data
        print(self, nodetree, depsgraph)
