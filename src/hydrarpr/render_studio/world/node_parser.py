# **********************************************************************
# Copyright 2023 Advanced Micro Devices, Inc
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
import math

import bpy

from . import log


def pass_node_reroute(link):
    while isinstance(link.from_node, bpy.types.NodeReroute):
        if not link.from_node.inputs[0].links:
            return None

        link = link.from_node.inputs[0].links[0]

    return link if link.is_valid else None

class NodeItem:
    """This class is a wrapper used for doing operations on MaterialX nodes, floats, and tuples"""

    def __init__(self, data: [tuple, float, dict]):
        self.data = data

    def node_item(self, value):
        if isinstance(value, NodeItem):
            return value

        return NodeItem(value)

    # MATH OPERATIONS
    def _arithmetic_helper(self, other, func):
        if other is None:
            if isinstance(self.data, float):
                result_data = func(self.data)
            elif isinstance(self.data, tuple):
                result_data = tuple(map(func, self.data))
            else:
                result_data = self.data

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
                result_data = other_data if isinstance(self.data, (float, tuple)) else self.data

        return self.node_item(result_data)

    def __add__(self, other):
        return self._arithmetic_helper(other, lambda a, b: a + b)

    def __sub__(self, other):
        return self._arithmetic_helper(other, lambda a, b: a - b)

    def __mul__(self, other):
        return self._arithmetic_helper(other, lambda a, b: a * b)

    def __truediv__(self, other):
        return self._arithmetic_helper(other, lambda a, b: a / b if not math.isclose(b, 0.0) else 0.0)

    def __mod__(self, other):
        return self._arithmetic_helper(other, lambda a, b: a % b)

    def __pow__(self, other):
        return self._arithmetic_helper(other, lambda a, b: a ** b)

    def __neg__(self):
        return 0.0 - self

    def __abs__(self):
        return self._arithmetic_helper(None, lambda a: abs(a))

    def floor(self):
        return self._arithmetic_helper(None, lambda a: float(math.floor(a)))

    def ceil(self):
        return self._arithmetic_helper(None, lambda a: float(math.ceil(a)))

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
        dot = self._arithmetic_helper(other, lambda a, b: a * b)
        if isinstance(dot.data, tuple):
            dot.data = sum(dot.data)

        return dot

    def if_else(self, cond: str, other, if_value, else_value):
        if cond == '>':
            res = self._arithmetic_helper(other, lambda a, b: float(a > b))
        elif cond == '>=':
            res = self._arithmetic_helper(other, lambda a, b: float(a >= b))
        elif cond == '==':
            res = self._arithmetic_helper(other, lambda a, b: float(a == b))
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
            return res

    def min(self, other):
        return self._arithmetic_helper(other, lambda a, b: min(a, b))

    def max(self, other):
        return self._arithmetic_helper(other, lambda a, b: max(a, b))

    def clamp(self, min_val=0.0, max_val=1.0):
        """ clamp data to min/max """
        return self.min(max_val).max(min_val)

    def sin(self):
        return self._arithmetic_helper(None, lambda a: math.sin(a))

    def cos(self):
        return self._arithmetic_helper(None, lambda a: math.cos(a))

    def tan(self):
        return self._arithmetic_helper(None, lambda a: math.tan(a))

    def asin(self):
        return self._arithmetic_helper(None, lambda a: math.asin(a))

    def acos(self):
        return self._arithmetic_helper(None, lambda a: math.acos(a))

    def atan(self):
        return self._arithmetic_helper(None, lambda a: math.atan(a))

    def log(self):
        return self._arithmetic_helper(None, lambda a: math.log(a))

    def blend(self, value1, value2):
        """ Line interpolate value between value1(0.0) and value2(1.0) by self.data as factor """
        return self * value2 + (1.0 - self) * value1


class NodeParser:
    """
    This is the base class that parses a blender node.
    Subclasses should override only export() function.
    """

    def __init__(self, world: bpy.types.World,
                 node: bpy.types.Node, out_key, **kwargs):
        self.world = world
        self.node = node
        self.out_key = out_key
        self.kwargs = kwargs

    @staticmethod
    def get_node_parser_cls(bl_idname):
        """ Returns NodeParser class for node_idname or None if not found """
        from . import nodes
        return getattr(nodes, bl_idname, None)

    # INTERNAL FUNCTIONS
    def _export_node(self, node, out_key, group_node=None):
        # getting corresponded NodeParser class
        NodeParser_cls = self.get_node_parser_cls(node.bl_idname)
        if not NodeParser_cls:
            log.warn("Ignoring unsupported node", node, self.world)
            return None

        node_parser = NodeParser_cls(self.world, node, out_key, **self.kwargs)
        return node_parser.export()

    def _parse_val(self, val):
        """Turn blender socket value into python's value"""

        if isinstance(val, (int, float)):
            return float(val)

        if len(val) in (3, 4):
            return tuple(val)

        if isinstance(val, str):
            return val

        raise TypeError("Unknown value type to parse", val)

    def node_item(self, value):
        if isinstance(value, NodeItem):
            return value

        return NodeItem(value)

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

        # check if linked is correct
        if not link.is_valid:
            log.warn("Invalid link ignored", link, socket_in, self.node, self.world)
            return None

        link = pass_node_reroute(link)
        if not link:
            return None

        return self._export_node(link.from_node, link.from_socket.identifier)

    def get_input_value(self, in_key):
        """ Returns linked node or default socket value """

        val = self.get_input_link(in_key)
        if val is not None:
            return val

        return self.get_input_default(in_key)

    def get_input_scalar(self, socket_key):
        """ Parse link, accept only RPR core material nodes """
        val = self.get_input_link(socket_key)
        if val is not None and isinstance(val.data, (float, tuple)):
            return val

        return self.get_input_default(socket_key)

    # EXPORT FUNCTION
    def export(self) -> [NodeItem, None]:
        """Main export function which should be overridable in child classes"""
        return None
