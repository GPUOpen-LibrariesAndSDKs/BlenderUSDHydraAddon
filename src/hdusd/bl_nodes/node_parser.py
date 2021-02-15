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
import bpy
import MaterialX as mx

from .node_item import NodeItem
from . import log


class NodeParser:
    """
    This is the base class that parses a blender node.
    Subclasses should override only export() function.
    """

    def __init__(self, doc: mx.Document, material: bpy.types.Material, node: bpy.types.Node,
                 obj: bpy.types.Object, out_key, group_nodes=(), **kwargs):
        self.doc = doc
        self.material = material
        self.node = node
        self.object = obj
        self.out_key = out_key
        self.group_nodes = group_nodes
        self.kwargs = kwargs

    @staticmethod
    def get_node_parser_cls(bl_idname):
        """ Returns NodeParser class for node_idname or None if not found """
        from . import nodes
        return getattr(nodes, bl_idname, None)

    # INTERNAL FUNCTIONS
    def _export_node(self, node, out_key, group_node=None):
        """
        Exports node with output socket.
        1. Checks if such node was already exported and returns it.
        2. Searches corresponded NodeParser class and do export through it
        3. Store group node reference if new one passed
        """
        # Keep reference for group node if present
        if group_node:
            if self.group_nodes:
                group_nodes = self.group_nodes + (group_node,)
            else:
                group_nodes = (group_node,)
        else:
            group_nodes = self.group_nodes

        # # check if this node was already parsed
        # node_key = key(self.material_key, node, socket_out, group_nodes)
        #
        # rpr_node = self.rpr_context.material_nodes.get(node_key, None)
        # if rpr_node:
        #     return rpr_node

        # getting corresponded NodeParser class
        NodeParser_cls = self.get_node_parser_cls(node.bl_idname)
        if NodeParser_cls:
            node_parser = NodeParser_cls(self.doc, self.material, node, out_key,
                                         group_nodes, **self.kwargs)
            return node_parser.final_export()

        log.warn("Ignoring unsupported node", node, self.material)
        return None

    def _parse_val(self, val):
        """Turn a blender node val or default value into something that works well with rpr """

        if isinstance(val, (int, float)):
            return float(val)

        if len(val) in (3, 4):
            return tuple(val)

        if isinstance(val, str):
            return val

        raise TypeError("Unknown value type to pass to rpr", val)

    # HELPER FUNCTIONS
    # Child classes should use them to do their export
    def get_output_default(self):
        """ Returns default value of output socket """
        socket_out = self.node.outputs[self.out_key]
        return self._parse_val(socket_out.default_value)

    def get_input_default(self, in_key):
        """ Returns default value of input socket """

        socket_in = self.node.inputs[in_key]
        return self._parse_val(socket_in.default_value)

    def get_input_link(self, in_key: [str, int]):
        """Returns linked parsed node or None if nothing is linked or not link is not valid"""

        socket_in = self.node.inputs[in_key]

        if not socket_in.is_linked:
            return None

        link = socket_in.links[0]

        # # check if linked is correct
        # if not self.is_link_allowed(link):
        #     raise MaterialError("Invalid link found", link, socket_in, self.node, self.material)

        result = self._export_node(link.from_node, link.from_socket.identifier)

        return result

    def get_input_value(self, in_key):
        """ Returns linked node or default socket value """

        val = self.get_input_link(in_key)
        if val is not None:
            return val

        return self.get_input_default(in_key)

    def node_item(self, mx_node_name, nd_type, inputs=None):
        node_item = NodeItem(
            self.doc, self.doc.addNode(mx_node_name, f"{mx_node_name}_{NodeItem.id()}", nd_type))
        if inputs:
            for name, (value, nd_type) in inputs.items():
                node_item.set_input(name, value, nd_type)

        return node_item

    # EXPORT FUNCTION
    def export(self) -> [NodeItem, None]:
        """Main export function which should be overridable in child classes"""
        return None

    def final_export(self):
        """
        This is the entry point of NodeParser classes.
        This function does some useful preparation before and after calling export() function.
        """
        log("export", self.object, self.material, self.node, self.out_key, self.group_nodes)

        return self.export()
