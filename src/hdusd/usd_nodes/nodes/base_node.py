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
from pxr import Usd

from . import log


class USDNode(bpy.types.Node):
    """Base class for parsing USD nodes"""

    bl_compatibility = {'HdUSD'}

    input_names = ("Input",)
    output_name = "Output"

    @classmethod
    def poll(cls, tree):
        return tree.bl_idname == 'hdusd.USDTree'

    def init(self, context):
        for name in self.input_names:
            self.safe_call(self.inputs.new, name=name, type="NodeSocketShader")

        if self.output_name:
            self.safe_call(self.outputs.new, name=self.output_name, type="NodeSocketShader")

    def safe_call(self, op, *args, **kwargs):
        """This function prevents call of nodetree.update() during calling our function"""
        self.id_data.is_node_safe_call = True
        try:
            op(*args, **kwargs)
        finally:
            self.id_data.is_node_safe_call = False

    # COMPUTE FUNCTION
    def compute(self, **kwargs) -> [Usd.Stage, None]:
        """
        Main compute function which should be overridable in child classes.
        It should return Prim object or None.
        """
        return None

    def final_compute(self, group_nodes=(), **kwargs):
        """
        This is the entry point of node parser system.
        This function does some useful preparation before and after calling compute() function.
        """
        log("compute", self, group_nodes)

        stage = self.cached_stage()
        if not stage:
            stage = self.compute(group_nodes=group_nodes, **kwargs)
            self.cached_stage.assign(stage)
            self.hdusd.usd_list.update_items()

        return stage

    def _compute_node(self, node, group_node=None, **kwargs):
        """
        Exports node with output socket.
        1. Checks if such node was already computeed and returns it.
        2. Searches corresponded NodeParser class and do compute through it
        3. Store group node reference if new one passed
        """
        # Keep reference for group node if present
        if not isinstance(node, USDNode):
            log.warn("Ignoring unsupported node", node)
            return None

        group_nodes = kwargs.pop('group_nodes', None)
        if group_node:
            if group_nodes:
                group_nodes += (group_node,)
            else:
                group_nodes = (group_node,)

        # getting corresponded NodeParser class
        return node.final_compute(group_nodes, **kwargs)

    # HELPER FUNCTIONS
    # Child classes should use them to do their compute

    def get_input_link(self, socket_key: [str, int], **kwargs):
        """Returns linked parsed node or None if nothing is linked or not link is not valid"""

        socket_in = self.inputs[socket_key]
        if not socket_in.links:
            return None

        link = socket_in.links[0]
        if not link.is_valid:
            log.error("Invalid link found", link, socket_in, self)

        # removing 'socket_out' from kwargs before transferring to _compute_node
        kwargs.pop('socket_out', None)
        return self._compute_node(link.from_node, **kwargs)

    @property
    def cached_stage(self):
        return self.hdusd.usd_list.cached_stage

    def free(self):
        self.cached_stage.clear()
