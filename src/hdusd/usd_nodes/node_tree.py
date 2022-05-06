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
from .nodes.print_file import PrintFileNode
from .nodes.write_file import WriteFileNode
from ..viewport import usd_collection
from ..engine.viewport_engine import ViewportEngineNodetree


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
    COMPAT_ENGINES = {'HdUSD'}

    _is_resetting = False
    _do_update = True

    @classmethod
    def poll(cls, context):
        return context.engine in cls.COMPAT_ENGINES

    def get_output_node(self, render_type='BOTH'):
        output_node = next((node for node in self.nodes if isinstance(node, HydraRenderNode) and \
                            node.render_type == render_type), None)

        if output_node:
            return output_node

        # try other output nodes
        secondary_output_node = next(
            (node for node in self.nodes if isinstance(node, (PrintFileNode, WriteFileNode))),
            None)

        return secondary_output_node

    def _reset_nodes(self, nodes, is_hard):
        self._is_resetting = True

        try:
            nodes = tuple(node for node in nodes if not isinstance(node, (bpy.types.NodeReroute, bpy.types.NodeFrame))
                          and (is_hard or node.use_hard_reset))

            for node in nodes:
                node.free()

            for node in nodes:
                node.final_compute()

        finally:
            self._is_resetting = False

    # this is called from Blender
    def update(self):
        if not self._do_update:
            return

        self._reset_nodes(self.nodes, False)

    def reset(self):
        self._reset_nodes(self.nodes, True)

    def depsgraph_update(self, depsgraph):
        if self._is_resetting:
            return

        for node in self.nodes:
            if not isinstance(node, (bpy.types.NodeReroute, bpy.types.NodeFrame)):
                node.depsgraph_update(depsgraph)

    def frame_change(self, depsgraph):
        if self._is_resetting:
            return

        for node in self.nodes:
            if not isinstance(node, (bpy.types.NodeReroute, bpy.types.NodeFrame)):
                node.frame_change(depsgraph)

    def material_update(self, depsgraph):
        if self._is_resetting:
            return

        for node in self.nodes:
            if not isinstance(node, (bpy.types.NodeReroute, bpy.types.NodeFrame)):
                node.material_update(depsgraph)

    def no_update_call(self, op, *args, **kwargs):
        """This function prevents call of self.update() during calling our function"""
        if not self._do_update:
            return op(*args, **kwargs)

        self._do_update = False
        try:
            return op(*args, **kwargs)
        finally:
            self._do_update = True

    def add_basic_nodes(self, source='SCENE'):
        """ Reset basic node tree structure using scene or USD file as an input """

        def create_nodes():
            self.nodes.clear()

            if source == 'USD_FILE':
                input_node = self.nodes.new("usd.UsdFileNode")
            else:  # default 'SCENE'
                input_node = self.nodes.new("usd.BlenderDataNode")
            input_node.location = (input_node.location[0] - 150, input_node.location[1])

            hydra_output = self.nodes.new("usd.HydraRenderNode")
            hydra_output.location = (hydra_output.location[0] + 150, hydra_output.location[1])

            self.links.new(input_node.outputs[0], hydra_output.inputs[0])

        self.no_update_call(create_nodes)
        self.reset()

    def output_node_computed(self):
        context = bpy.context
        if context.scene.hdusd.viewport.data_source == self.name:
            context.scene.hdusd.viewport.nodetree_update(context)
            usd_collection.update(context)

        if context.scene.hdusd.final.data_source == self.name:
            context.scene.hdusd.final.nodetree_update(context)

        ViewportEngineNodetree.nodetree_output_node_computed(self)


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
    return next((nodetree for nodetree in bpy.data.node_groups if isinstance(nodetree, USDTree)),
                None)


def reset():
    for nodetree in bpy.data.node_groups:
        if isinstance(nodetree, USDTree):
            nodetree.reset()


def depsgraph_update(depsgraph):
    for nodetree in bpy.data.node_groups:
        if isinstance(nodetree, USDTree):
            nodetree.depsgraph_update(depsgraph)


def frame_change(depsgraph):
    for nodetree in bpy.data.node_groups:
        if isinstance(nodetree, USDTree):
            nodetree.frame_change(depsgraph)


def material_update(material):
    for nodetree in bpy.data.node_groups:
        if isinstance(nodetree, USDTree):
            nodetree.material_update(material)
