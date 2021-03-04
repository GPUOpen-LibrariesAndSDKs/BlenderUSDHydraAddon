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
import MaterialX as mx

from . import title_str


def set_param_value(mx_param, val, nd_type):
    if isinstance(val, mx.Node):
        mx_param.setNodeName(val.getName())
    elif nd_type == 'filename':
        mx_param.setValueString(val)
    else:
        mx_type = getattr(mx, title_str(nd_type), None)
        if mx_type:
            mx_param.setValue(mx_type(val))
        else:
            mx_param.setValue(val)


def is_value_equal(mx_val, val, nd_type):
    if nd_type in ('string', 'float', 'integer', 'boolean', 'filename'):
        return mx_val == val

    return tuple(mx_val) == tuple(val)


def is_shader_type(mx_type):
    return not (mx_type in ('string', 'float', 'integer', 'boolean', 'filename') or
                mx_type.startswith('color') or
                mx_type.startswith('vector') or
                mx_type.endswith('array'))


def parse_value(mx_val, mx_type):
    if mx_type in ('string', 'float', 'integer', 'boolean', 'filename'):
        return mx_val

    return tuple(mx_val)


def parse_value_str(val_str, mx_type, *, first_only=False, is_enum=False):
    if mx_type == 'string':
        if is_enum:
            res = tuple(x.strip() for x in val_str.split(','))
            return res[0] if first_only else res
        return val_str

    if mx_type == 'integer':
        return int(val_str)
    if mx_type == 'float':
        return float(val_str)
    if mx_type == 'boolean':
        return val_str == "true"
    if mx_type.endswith('array'):
        return val_str

    if mx_type.startswith('color') or mx_type.startswith('vector') or mx_type.startswith('matrix'):
        res = tuple(float(x) for x in val_str.split(','))
        return res[0] if first_only else res

    return val_str
