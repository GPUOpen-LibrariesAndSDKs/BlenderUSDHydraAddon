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
    bl_width_default = 200

    input_names = ("Input",)
    output_name = "Output"
    use_hard_reset = True

    @classmethod
    def poll(cls, tree):
        return tree.bl_idname == 'hdusd.USDTree'

    def init(self, context):
        def init_():
            for name in self.input_names:
                self.inputs.new(name=name, type="NodeSocketShader")

            if self.output_name:
                self.outputs.new(name=self.output_name, type="NodeSocketShader")

        self.id_data.safe_call(init_)

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
        stage = self.cached_stage()
        if not stage:
            log("compute", self, group_nodes)
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
            log.warn("Invalid link found", link, socket_in, self)

        # removing 'socket_out' from kwargs before transferring to _compute_node
        kwargs.pop('socket_out', None)
        return self._compute_node(link.from_node, **kwargs)

    @property
    def cached_stage(self):
        return self.hdusd.usd_list.cached_stage

    def free(self):
        self.cached_stage.clear()

    def reset(self, is_hard=False):
        if is_hard or self.use_hard_reset:
            log("reset", self)

            self.free()
            self.final_compute()
            self.hdusd.usd_list.update_items()

        self._reset_next(is_hard)

    def _reset_next(self, is_hard):
        for output in self.outputs:
            for link in output.links:
                link.to_node.reset(is_hard)

    def depsgraph_update(self, depsgraph):
        pass
