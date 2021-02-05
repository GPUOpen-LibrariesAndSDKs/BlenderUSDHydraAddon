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

    def __init__(self, parse_type, material: bpy.types.Material, node: bpy.types.Node,
                 obj: bpy.types.Object, out_key, group_nodes=(), **kwargs):
        self.material = material
        self.node = node
        self.object = obj
        self.out_key = out_key
        self.group_nodes = group_nodes
        self.kwargs = kwargs

    @property
    def mx_doc(self):
        return self.kwargs['mx_doc']

    # INTERNAL FUNCTIONS

    def _export_node(self, node, socket_out, group_node=None):
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

        # check if this node was already parsed
        node_key = key(self.material_key, node, socket_out, group_nodes)

        rpr_node = self.rpr_context.material_nodes.get(node_key, None)
        if rpr_node:
            return rpr_node

        # getting corresponded NodeParser class
        node_parser_class = get_node_parser_class(node.bl_idname)
        if node_parser_class:
            node_parser = node_parser_class(self.rpr_context, self.material, node, socket_out,
                                            group_nodes, data=self.data)
            return node_parser.final_export()

        log.warn("Ignoring unsupported node", node, self.material)
        return None

    def _parse_val(self, val):
        """ Turn a blender node val or default value for input into something that works well with rpr """

        if isinstance(val, (int, float)):
            return float(val)

        if len(val) in (3, 4):
            return tuple(val)

        if isinstance(val, str):
            return val

        raise TypeError("Unknown value type to pass to rpr", val)

    # HELPER FUNCTIONS
    # Child classes should use them to do their export

    def get_output_default(self, socket_key=None):
        """ Returns default value of output socket """

        socket_out = self.socket_out if socket_key is None else self.node.outputs[socket_key]
        return self._parse_val(socket_out.default_value)

    def get_input_default(self, socket_key):
        """ Returns default value of input socket """

        socket_in = self.node.inputs[socket_key]
        return self._parse_val(socket_in.default_value)

    def get_input_link(self, socket_key: [str, int], accepted_type=None):
        """
        Returns linked parsed node or None if nothing is linked or not link is not valid
        :arg socket_key: socket name to parse in current node
        :arg accepted_type: accepted types result filter, optional
        :type accepted_type: class, tuple or None
        """

        socket_in = self.node.inputs[socket_key]

        if socket_in.is_linked:
            link = socket_in.links[0]

            # check if linked is correct
            if not self.is_link_allowed(link):
                raise MaterialError("Invalid link found", link, socket_in, self.node, self.material)

            result = self._export_node(link.from_node, link.from_socket)

            # check if result type is allowed by acceptance filter
            if accepted_type and not isinstance(result, accepted_type):
                return None

            return result

        return None

    def get_input_normal(self, socket_key):
        """ Parse link, accept only RPR core material nodes """
        input_normal = self.get_input_link(socket_key, accepted_type=pyrpr.MaterialNode)
        return input_normal if input_normal is not None else self.normal_node

    @staticmethod
    def is_link_allowed(link):
        """
        Check if linked socket could be linked to destination socket
        Some links are not allowed for RPR, like any shader to non-shader
        """

        # link loop
        if not link.is_valid:
            return False

        source = link.from_socket
        destination = link.to_socket

        is_source_shader = isinstance(source, bpy.types.NodeSocketShader)
        is_destination_shader = isinstance(destination, bpy.types.NodeSocketShader)

        # Linking shaders and non-shaders
        if is_source_shader ^ is_destination_shader:
            return False

        return True

    def get_input_value(self, socket_key):
        """ Returns linked node or default socket value """

        val = self.get_input_link(socket_key)
        if val is not None:
            return val

        return self.get_input_default(socket_key)

    def get_input_scalar(self, socket_key):
        """ Parse link, accept only RPR core material nodes """
        val = self.get_input_link(socket_key, accepted_type=(float, tuple))
        if val is not None:
            return val

        return self.get_input_default(socket_key)

    def create_node(self, material_type, inputs={}):
        rpr_node = self.rpr_context.create_material_node(material_type)
        for name, value in inputs.items():
            rpr_node.set_input(name, value)

        return rpr_node

    def create_arithmetic(self, op_type, color1, color2=None, color3=None):
        rpr_node = self.create_node(pyrpr.MATERIAL_NODE_ARITHMETIC, {
            pyrpr.MATERIAL_INPUT_OP: op_type,
            pyrpr.MATERIAL_INPUT_COLOR0: color1
        })
        if color2:
            rpr_node.set_input(pyrpr.MATERIAL_INPUT_COLOR1, color2)
        if color3:
            rpr_node.set_input(pyrpr.MATERIAL_INPUT_COLOR2, color3)

        return rpr_node

    # EXPORT FUNCTION
    @abstractmethod
    def export(self):
        """
        Main export function which should be overridable in child classes.
        Example:
            color = self.get_input_value('Color')
            normal = self.get_input_link('Normal')

            node = self.create_node(pyrpr.MATERIAL_NODE_REFLECTION, {
                'color': color
            })
            if normal:
                node.set_input(pyrpr.MATERIAL_INPUT_NORMAL, normal)

            return node
        """
        pass

    def export_muted(self):
        # export as a muted node
        # pass through first linked socket of same output socket type
        matching_incoming_socket = next((input for input in self.node.inputs
            if isinstance(input, type(self.socket_out)) and input.is_linked), None)
        if matching_incoming_socket:
            return self.get_input_link(matching_incoming_socket.name)
        else:
            # if no inputs use the socket val
            return None

    def final_export(self):
        """
        This is the entry point of NodeParser classes.
        This function does some useful preparation before and after calling export() function.
        """

        log("export", self.material, self.node, self.socket_out, self.group_nodes)
        
        if self.node.mute:
            rpr_node = self.export_muted()
        else:
            rpr_node = self.export()

        if isinstance(rpr_node, pyrpr.MaterialNode):
            node_key = key(self.material_key, self.node, self.socket_out, self.group_nodes)
            self.rpr_context.set_material_node_key(node_key, rpr_node)
            rpr_node.set_name(str(node_key))

        return rpr_node


def get_node_parser_class(node_idname: str):
    """ Returns NodeParser class for node_idname or None if not found """

    from . import nodes
    parser_class = getattr(nodes, node_idname, None)
    if parser_class:
        return parser_class

    return None
