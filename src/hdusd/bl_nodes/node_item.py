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
import MaterialX as mx

from ..utils import set_mx_param_value


class NodeItem:
    """This class is a wrapper used for doing operations on MaterialX nodes"""
    id = 0
    
    def __init__(self, doc:mx.Document, data: [tuple, float, mx.Node]):
        # save the data as vec4 if num data
        self.data = data
        self.doc = doc

    def set_input(self, name, value):
        if value is not None:
            self.data.set_input(name, value.data if isinstance(value, NodeItem) else value)

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
                result_data = self.doc.addNode(op_node, f"{op_node}_{NodeItem.id}",
                                               self.data.getType())
                input = result_data.addInput('in', self.data.getType())
                set_mx_param_value(input, self.data, self.data.getType())
                NodeItem.id += 1

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
                result_data = self.doc.addNode(op_node, f"{op_node}_{NodeItem.id}",
                                               self.data.getType())
                input1 = result_data.addInput('in1', self.data.getType())
                set_mx_param_value(input1, self.data, self.data.getType())
                input2 = result_data.addInput('in2', self.data.getType())
                set_mx_param_value(input2, other_data, self.data.getType())
                NodeItem.id += 1

        return NodeItem(self.doc, result_data)

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
        f = self.floor()
        return (self == f).if_else(self, f + 1.0)

    def fract(self):
        return self - self.floor()

    # right hand methods for doing something like 1.0 - Node
    def __radd__(self, other):
        return self + other
        
    def __rsub__(self, other):
        if not isinstance(other, NodeItem):
            other = NodeItem(self.doc, other)
        return other - self

    def __rmul__(self, other):
        return self * other

    def __rtruediv__(self, other):
        if not isinstance(other, NodeItem):
            other = NodeItem(self.doc, other)
        return other / self

    def __rmod__(self, other):
        if not isinstance(other, NodeItem):
            other = NodeItem(self.doc, other)
        return other % self

    def __rpow__(self, other):
        if not isinstance(other, NodeItem):
            other = NodeItem(self.doc, other)
        return other ** self

    def dot(self, other):
        dot = self._arithmetic_helper(other, 'dotproduct', lambda a, b: a * b)
        if isinstance(dot.data, tuple):
            dot.data = sum(dot.data)

        return dot

    # def if_else(self, cond, other, if_value, else_value):
    #     other_data = other.data if isinstance(other, NodeItem) else other
    #     if_data = if_value.data if isinstance(if_value, NodeItem) else if_value
    #     else_data = else_value.data if isinstance(else_value, NodeItem) else else_value
    #
    #     if isinstance(self.data, float):
    #         result_data = if_data if bool(self.data) else else_data
    #     else:
    #         result_data = self.rpr_context.create_material_node(pyrpr.MATERIAL_NODE_ARITHMETIC)
    #         result_data.set_input(pyrpr.MATERIAL_INPUT_OP, pyrpr.MATERIAL_NODE_OP_TERNARY)
    #         result_data.set_input(pyrpr.MATERIAL_INPUT_COLOR0, self.data)
    #         result_data.set_input(pyrpr.MATERIAL_INPUT_COLOR1, if_data)
    #         result_data.set_input(pyrpr.MATERIAL_INPUT_COLOR2, else_data)
    #
    #     return NodeItem(self.rpr_context, result_data)
    #
    # def __gt__(self, other):
    #     return self._arithmetic_helper(other, 'ifgreater',
    #                                    lambda a, b: float(a > b))
    #
    # def __ge__(self, other):
    #     return self._arithmetic_helper(other, 'ifgreatereq',
    #                                    lambda a, b: float(a >= b))
    #
    # def __lt__(self, other):
    #     if not isinstance(other, NodeItem):
    #         other = NodeItem(self.doc, other)
    #     return other >= self
    #
    # def __le__(self, other):
    #     if not isinstance(other, NodeItem):
    #         other = NodeItem(self.doc, other)
    #     return other > self
    #
    # def __eq__(self, other):
    #     return self._arithmetic_helper(other, 'ifequal',
    #                                    lambda a, b: float(a == b))
    #
    # def __ne__(self, other):
    #     return 1.0 - (self == other)

    def min(self, other):
        return self._arithmetic_helper(other, 'min', lambda a, b: min(a, b))

    def max(self, other):
        return self._arithmetic_helper(other, 'max', lambda a, b: max(a, b))

    def clamp(self, min_val=0.0, max_val=1.0):
        ''' clamp data to min/max '''
        return self.min(max_val).max(min_val)

    def sin(self):
        return self._arithmetic_helper(None, 'sin', lambda a: math.sin(a))

    def cos(self):
        return self._arithmetic_helper(None, 'cos', lambda a: math.cos(a))

    def tan(self):
        return self._arithmetic_helper(None, 'tan', lambda a: math.tan(a))
