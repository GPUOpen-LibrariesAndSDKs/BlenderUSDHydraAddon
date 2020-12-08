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
