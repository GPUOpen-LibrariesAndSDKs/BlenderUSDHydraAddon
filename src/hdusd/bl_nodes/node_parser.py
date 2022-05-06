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
import math

import bpy
import MaterialX as mx

from ..utils import mx as mx_utils
from ..utils import pass_node_reroute
from ..mx_nodes.nodes import get_mx_node_cls 
from . import log


OUTPUT_TYPE = {'RGBA': 'color3',
               'VALUE': 'float',
               'VECTOR': 'vector3'}


class Id:
    def __init__(self):
        self.id = 0

    def __call__(self):
        self.id += 1
        return self.id


class NodeItem:
    """This class is a wrapper used for doing operations on MaterialX nodes, floats, and tuples"""

    def __init__(self, id: Id, ng: [mx.Document, mx.NodeGraph], data: [tuple, float, mx.Node]):
        self.id = id
        self.nodegraph = ng
        self.data = data
        self.nodedef = None
        if isinstance(data, mx.Node):
            MxNode_cls, _ = get_mx_node_cls(data)
            self.nodedef = MxNode_cls.get_nodedef(self.type)

    def node_item(self, value):
        if isinstance(value, NodeItem):
            return value

        return NodeItem(self.id, self.nodegraph, value)

    @property
    def type(self):
        if isinstance(self.data, float):
            return 'float_'
        elif isinstance(self.data, tuple):
            return 'tuple_'
        else:
            return self.data.getType()

    def set_input(self, name, value):
        if value is None:
            return

        val_data = value.data if isinstance(value, NodeItem) else value
        nd_input = self.nodedef.getInput(name)
        input = self.data.addInput(name, nd_input.getType())
        mx_utils.set_param_value(input, val_data, input.getType())

    def set_inputs(self, inputs):
        for name, value in inputs.items():
            self.set_input(name, value)

    # MATH OPERATIONS
    def _arithmetic_helper(self, other, op_node, func):
        ''' helper function for overridden math functions.
            This simply creates an arithmetic node of rpr_type
            if one of the operands has node data, else maps the function to data '''

        if other is None:
            if isinstance(self.data, float):
                result_data = func(self.data)
            elif isinstance(self.data, tuple):
                result_data = tuple(map(func, self.data))
            else:
                result_data = self.nodegraph.addNode(op_node, f"{op_node}_{self.id()}",
                                                     self.data.getType())
                input = result_data.addInput('in', self.data.getType())
                mx_utils.set_param_value(input, self.data, self.data.getType())

        else:
            other_data = other.data if isinstance(other, NodeItem) else other
            if isinstance(self.data, (float, tuple)) and isinstance(other_data, (float, tuple)):
                if isinstance(self.data, float) and isinstance(other_data, float):
                    result_data = func(self.data, other_data)
                else:
                    data = self.data

                    # converting data or other_data to have equal length
                    if isinstance(data, float):
                        data = (data,) * len(other_data)
                    elif isinstance(other_data, float):
                        other_data = (other_data,) * len(data)
                    elif len(data) < len(other_data):
                        data = (*data, 1.0)
                    elif len(other_data) < len(data):
                        other_data = (*other_data, 1.0)

                    result_data = tuple(map(func, data, other_data))

            else:
                nd_type = self.data.getType() if isinstance(self.data, mx.Node) else \
                          other_data.getType()

                result_data = self.nodegraph.addNode(op_node, f"{op_node}_{self.id()}", nd_type)
                input1 = result_data.addInput('in1', nd_type)
                mx_utils.set_param_value(input1, self.data, nd_type)
                input2 = result_data.addInput('in2', nd_type)
                mx_utils.set_param_value(input2, other_data, nd_type)

        return self.node_item(result_data)

    def __add__(self, other):
        return self._arithmetic_helper(other, 'add', lambda a, b: a + b)

    def __sub__(self, other):
        return self._arithmetic_helper(other, 'subtract', lambda a, b: a - b)

    def __mul__(self, other):
        return self._arithmetic_helper(other, 'multiply', lambda a, b: a * b)

    def __truediv__(self, other):
        return self._arithmetic_helper(other, 'divide',
                                       lambda a, b: a / b if not math.isclose(b, 0.0) else 0.0)

    def __mod__(self, other):
        return self._arithmetic_helper(other, 'modulo', lambda a, b: a % b)

    def __pow__(self, other):
        return self._arithmetic_helper(other, 'power', lambda a, b: a ** b)

    def __neg__(self):
        return 0.0 - self

    def __abs__(self):
        return self._arithmetic_helper(None, 'absval', lambda a: abs(a))

    def floor(self):
        return self._arithmetic_helper(None, 'floor', lambda a: float(math.floor(a)))

    def ceil(self):
        return self._arithmetic_helper(None, 'ceil', lambda a: float(math.ceil(a)))

    # right hand methods for doing something like 1.0 - Node
    def __radd__(self, other):
        return self + other

    def __rsub__(self, other):
        return self.node_item(other) - self

    def __rmul__(self, other):
        return self * other

    def __rtruediv__(self, other):
        return self.node_item(other) / self

    def __rmod__(self, other):
        return self.node_item(other) % self

    def __rpow__(self, other):
        return self.node_item(other) ** self

    def dot(self, other):
        dot = self._arithmetic_helper(other, 'dotproduct', lambda a, b: a * b)
        if isinstance(dot.data, tuple):
            dot.data = sum(dot.data)

        return dot

    def if_else(self, cond: str, other, if_value, else_value):
        if cond == '>':
            res = self._arithmetic_helper(other, 'ifgreater', lambda a, b: float(a > b))
        elif cond == '>=':
            res = self._arithmetic_helper(other, 'ifgreatereq', lambda a, b: float(a >= b))
        elif cond == '==':
            res = self._arithmetic_helper(other, 'ifequal', lambda a, b: float(a == b))
        elif cond == '<':
            return self.node_item(other).if_else('>', self, else_value, if_value)
        elif cond == '<=':
            return self.node_item(other).if_else('>=', self, else_value, if_value)
        elif cond == '!=':
            return self.if_else('==', other, else_value, if_value)
        else:
            raise ValueError("Incorrect condition:", cond)

        if isinstance(res.data, float):
            return if_value if res.data == 1.0 else else_value
        elif isinstance(res.data, tuple):
            return if_value if res.data[0] == 1.0 else else_value
        else:
            res.set_input('value1', if_value)
            res.set_input('value2', else_value)
            return res

    def min(self, other):
        return self._arithmetic_helper(other, 'min', lambda a, b: min(a, b))

    def max(self, other):
        return self._arithmetic_helper(other, 'max', lambda a, b: max(a, b))

    def clamp(self, min_val=0.0, max_val=1.0):
        """ clamp data to min/max """
        return self.min(max_val).max(min_val)

    def sin(self):
        return self._arithmetic_helper(None, 'sin', lambda a: math.sin(a))

    def cos(self):
        return self._arithmetic_helper(None, 'cos', lambda a: math.cos(a))

    def tan(self):
        return self._arithmetic_helper(None, 'tan', lambda a: math.tan(a))

    def asin(self):
        return self._arithmetic_helper(None, 'asin', lambda a: math.asin(a))

    def acos(self):
        return self._arithmetic_helper(None, 'acos', lambda a: math.acos(a))

    def atan(self):
        return self._arithmetic_helper(None, 'atan', lambda a: math.atan(a))

    def log(self):
        return self._arithmetic_helper(None, 'ln', lambda a: math.log(a))

    def blend(self, value1, value2):
        """ Line interpolate value between value1(0.0) and value2(1.0) by self.data as factor """
        return self * value2 + (1.0 - self) * value1


class NodeParser:
    """
    This is the base class that parses a blender node.
    Subclasses should override only export() function.
    """

    nodegraph_path = "NG"

    def __init__(self, id: Id, doc: mx.Document, material: bpy.types.Material,
                 node: bpy.types.Node, obj: bpy.types.Object, out_key, output_type, cached_nodes,
                 group_nodes=(), **kwargs):
        self.id = id
        self.doc = doc
        self.material = material
        self.node = node
        self.object = obj
        self.out_key = out_key
        self.out_type = output_type
        self.cached_nodes = cached_nodes
        self.group_nodes = group_nodes
        self.kwargs = kwargs

    @staticmethod
    def get_output_type(to_socket):
        # Need to check ShaderNodeNormalMap separately because
        # if has input color3 type but materialx normalmap got vector3
        return 'vector3' if to_socket.node.type == 'NORMAL_MAP' else OUTPUT_TYPE.get(to_socket.type, 'color3')

    @staticmethod
    def get_node_parser_cls(bl_idname):
        """ Returns NodeParser class for node_idname or None if not found """
        from . import nodes
        return getattr(nodes, bl_idname, None)

    # INTERNAL FUNCTIONS
    def _export_node(self, node, out_key, to_socket, group_node=None):
        if group_node:
            if self.group_nodes:
                group_nodes = self.group_nodes + (group_node,)
            else:
                group_nodes = (group_node,)
        else:
            group_nodes = self.group_nodes

        # dynamically define output type of node
        output_type = self.get_output_type(to_socket)

        # check if this node was already parsed and cached
        node_item = self.cached_nodes.get((node.name, out_key, output_type))
        if node_item:
            return node_item

        # getting corresponded NodeParser class
        NodeParser_cls = self.get_node_parser_cls(node.bl_idname)
        if not NodeParser_cls:
            log.warn(f"Ignoring unsupported node {node.bl_idname}", node, self.material)
            self.cached_nodes[(node.name, out_key, output_type)] = None
            return None

        node_parser = NodeParser_cls(self.id, self.doc, self.material, node, self.object,
                                     out_key, output_type, self.cached_nodes, group_nodes, **self.kwargs)

        node_item = node_parser.export()

        self.cached_nodes[(node.name, out_key, output_type)] = node_item
        return node_item

    def _parse_val(self, val):
        """Turn blender socket value into python's value"""

        if isinstance(val, (int, float)):
            return float(val)

        if len(val) in (3, 4):
            return tuple(val)

        if isinstance(val, str):
            return val

        raise TypeError("Unknown value type to pass to rpr", val)

    def node_item(self, value):
        if isinstance(value, NodeItem):
            return value

        nodegraph = mx_utils.get_nodegraph_by_path(self.doc, self.nodegraph_path, True)
        return NodeItem(self.id, nodegraph, value)

    # HELPER FUNCTIONS
    # Child classes should use them to do their export
    def get_output_default(self):
        """ Returns default value of output socket """
        socket_out = self.node.outputs[self.out_key]

        return self.node_item(self._parse_val(socket_out.default_value))

    def get_input_default(self, in_key):
        """ Returns default value of input socket """

        socket_in = self.node.inputs[in_key]
        return self.node_item(self._parse_val(socket_in.default_value))

    def get_input_link(self, in_key: [str, int]):
        """Returns linked parsed node or None if nothing is linked or not link is not valid"""

        socket_in = self.node.inputs[in_key]
        if not socket_in.links:
            return None

        link = socket_in.links[0]

        if not link.is_valid:
            log.warn("Invalid link ignored", link, socket_in, self.node, self.material)
            return None

        link = pass_node_reroute(link)
        if not link:
            return None

        return self._export_node(link.from_node, link.from_socket.identifier, link.to_socket)

    def get_input_value(self, in_key):
        """ Returns linked node or default socket value """

        val = self.get_input_link(in_key)
        if val is not None:
            return val

        return self.get_input_default(in_key)

    def create_node(self, node_name, nd_type, inputs=None):
        nodegraph = mx_utils.get_nodegraph_by_path(self.doc, self.nodegraph_path, True)
        node = nodegraph.addNode(node_name, f"{node_name}_{self.id()}", nd_type)
        node_item = NodeItem(self.id, nodegraph, node)

        if inputs:
            node_item.set_inputs(inputs)

        return node_item

    # EXPORT FUNCTION
    def export(self) -> [NodeItem, None]:
        """Main export function which should be overridable in child classes"""
        return None
