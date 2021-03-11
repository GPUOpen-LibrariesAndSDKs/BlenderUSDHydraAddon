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
import re

import MaterialX as mx

from . import title_str

from . import logging
log = logging.Log(tag='utils.mx')


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


def get_attr(mx_param, name, else_val=None):
    return mx_param.getAttribute(name) if mx_param.hasAttribute(name) else else_val


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


def get_property_code(mx_param):
    mx_type = mx_param.getType()
    prop_attrs = {}

    prop_attrs['name'] = mx_param.getAttribute('uiname') if mx_param.hasAttribute('uiname') \
                         else title_str(mx_param.getName())
    prop_attrs['description'] = mx_param.getAttribute('doc')

    while True:     # one way loop just for having break instead using nested 'if else'
        if mx_type == 'string':
            if mx_param.hasAttribute('enum'):
                prop_type = "EnumProperty"
                items = parse_value_str(mx_param.getAttribute('enum'), mx_type, is_enum=True)
                prop_attrs['items'] = tuple((it, title_str(it), title_str(it)) for it in items)
                break
            prop_type = "StringProperty"
            break
        if mx_type == 'filename':
            prop_type = "StringProperty"
            prop_attrs['subtype'] = 'FILE_PATH'
            break
        if mx_type == 'integer':
            prop_type = "IntProperty"
            break
        if mx_type == 'float':
            prop_type = "FloatProperty"
            break
        if mx_type == 'boolean':
            prop_type = "BoolProperty"
            break
        if mx_type in ('surfaceshader', 'displacementshader', 'volumeshader', 'lightshader',
                       'material', 'BSDF', 'VDF', 'EDF'):
            prop_type = "StringProperty"
            break

        m = re.fullmatch('matrix(\d)(\d)', mx_type)
        if m:
            prop_type = "FloatVectorProperty"
            prop_attrs['subtype'] = 'MATRIX'
            prop_attrs['size'] = int(m[1]) * int(m[2])
            break

        m = re.fullmatch('color(\d)', mx_type)
        if m:
            prop_type = "FloatVectorProperty"
            prop_attrs['subtype'] = 'COLOR'
            prop_attrs['size'] = int(m[1])
            prop_attrs['soft_min'] = 0.0
            prop_attrs['soft_max'] = 1.0
            break

        m = re.fullmatch('vector(\d)', mx_type)
        if m:
            prop_type = "FloatVectorProperty"
            dim = int(m[1])
            prop_attrs['subtype'] = 'XYZ' if dim == 3 else 'NONE'
            prop_attrs['size'] = dim
            break

        m = re.fullmatch('(.+)array', mx_type)
        if m:
            prop_type = "StringProperty"
            # TODO: Change to CollectionProperty
            break

        prop_type = "StringProperty"
        log.warn("Unsupported mx_type", mx_type, mx_param, mx_param.getParent().getName())
        break

    for mx_attr, prop_attr in (('uimin', 'min'), ('uimax', 'max'),
                               ('uisoftmin', 'soft_min'), ('uisoftmax', 'soft_max'),
                               ('value', 'default')):
        if mx_param.hasAttribute(mx_attr):
            prop_attrs[prop_attr] = parse_value_str(
                mx_param.getAttribute(mx_attr), mx_type, first_only=mx_attr != 'value')

    prop_attr_strings = []
    for name, val in prop_attrs.items():
        val_str = f"'{val}'" if isinstance(val, str) else str(val)
        prop_attr_strings.append(f"{name}={val_str}")

    return f"{prop_type}({', '.join(prop_attr_strings)})"


def nodedef_data_type(nodedef):
    # nodedef name consists: ND_{node_name}_{data_type} therefore:
    res = nodedef.getName()[(4 + len(nodedef.getNodeString())):]
    if not res:
        res = nodedef.getOutputs()[0].getType()

    return res
