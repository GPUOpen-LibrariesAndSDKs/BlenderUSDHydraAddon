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

from .nodes.hydra_render import HydraRenderNode


class USDTree(bpy.types.ShaderNodeTree):
    """
    Holds hierarchy of data and composition of USD for rendering
    The basic (default) graph should be simply
    
    Read Blender Data (scene) ---> Hydra Render 

    When nodes or tree is updated, the node computation is re-run
    """
    bl_label = "USD"
    bl_icon = 'NODETREE'
    bl_idname = 'hdusd.USDTree'

    def get_output_node(self, render_type='BOTH'):
        return next((node for node in self.nodes if isinstance(node, HydraRenderNode) and \
                     node.render_type == render_type), None)

    def update(self):
        context = bpy.context
        usd_list = context.scene.hdusd.usd

        # calculating USD stage
        stage = None
        output_node = self.get_output_node()
        if output_node:
            depsgraph = context.evaluated_depsgraph_get()
            stage = output_node.final_compute('Input',
                depsgraph=depsgraph)

        usd_list.clear()
        if stage:
            for prim in stage.Traverse():
                item = usd_list.add()
                item.name = str(prim.GetPath())


class RenderTaskTree(bpy.types.ShaderNodeTree):
    """
    Hydra Tasks needed for rendering.  
    The outputs of this will be AOV's passed to blender.
    The default tree is simply Hydra Render -> outputs, but other options
    could be denoising, bloom filters, tone mapping, etc
    """
    bl_label = "Hydra Render"
    bl_icon = "NODETREE"
    bl_idname = "usd.RenderTaskTree"


def get_usd_nodetree():
    ''' return first USD nodetree found '''
    return next((ng for ng in bpy.data.node_groups if isinstance(ng, USDTree)), None)
