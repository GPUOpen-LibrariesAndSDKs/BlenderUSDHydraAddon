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
