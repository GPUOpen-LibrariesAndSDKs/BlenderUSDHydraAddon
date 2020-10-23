#**********************************************************************
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
#********************************************************************
from . import HDUSD_Panel
from ..usd_nodes.node_tree import get_usd_nodetree

class HDUSD_RENDER_PT_delegate_final(HDUSD_Panel):
    """
    Final Render Delegate and settings
    """
    bl_label = "Final Renderer"
    bl_context = 'render'

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        layout.prop(scene.hdusd.final, "delegate")

        # use the USD nodegraph if present
        row = layout.row()
        row.prop(scene.hdusd.final, "use_usd_nodegraph")
        row.enabled = get_usd_nodetree() is not None

class HDUSD_RENDER_PT_delegate_viewport(HDUSD_Panel):
    """
    Viewport Render Delegate and settings
    """
    bl_label = "Viewport Renderer"
    bl_context = 'render'

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        layout.prop(scene.hdusd.viewport, "delegate")

        # use the USD nodegraph if present
        row = layout.row()
        row.prop(scene.hdusd.viewport, "use_usd_nodegraph")
        row.enabled = get_usd_nodetree() is not None
