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
