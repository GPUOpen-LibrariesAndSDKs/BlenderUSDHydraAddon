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

from . import log


class ReadBlendDataNode(USDNode):
    """Blender data to USD can export whole scene, one collection or object"""
    bl_idname = 'usd.ReadBlendDataNode'
    bl_label = "Read Blend Data"

    input_names = ()

    def update_export_data(self, context):
        depsgraph = bpy.context.evaluated_depsgraph_get()
        
        self.id_data.reset()

    export_type: bpy.props.EnumProperty(
        name="Data to Read",
        description="",
        items=(('SCENE', "Scene", "Read entire scene"),
            ('COLLECTION', "Collection", "Read collection"),
            ('OBJECT', 'Object', "Read single object"),
        ),
        default='SCENE',
        update=update_export_data
    )

    collection_to_export: bpy.props.PointerProperty(
        type=bpy.types.Collection,
        name="Collection",
        description="",
        update=update_export_data
    )
    
    object_to_export: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Object",
        description="",
        update=update_export_data
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
        stage = self.cached_stage()
        if not stage:
            self.final_compute()
            return

        dp.sync_update(stage, depsgraph)
