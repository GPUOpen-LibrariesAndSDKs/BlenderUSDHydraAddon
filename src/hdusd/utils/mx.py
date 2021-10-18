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
import bpy

from .image import cache_image_file

from pathlib import Path

from . import LIBS_DIR, title_str, code_str

from . import logging
log = logging.Log(tag='utils.mx')


MX_LIBS_DIR = LIBS_DIR / "materialx/libraries"


def set_param_value(mx_param, val, nd_type, nd_output=None):
    if isinstance(val, mx.Node):
        param_nodegraph = mx_param.getParent().getParent()
        val_nodegraph = val.getParent()
        node_name = val.getName()
        if val_nodegraph == param_nodegraph:
            mx_param.setNodeName(node_name)
            if nd_output:
                mx_param.setAttribute('output', nd_output.getName())
        else:
            # checking nodegraph paths
            val_ng_path = val_nodegraph.getNamePath()
            param_ng_path = param_nodegraph.getNamePath()
            ind = val_ng_path.rfind('/')
            ind = ind if ind >= 0 else 0
            if param_ng_path != val_ng_path[:ind]:
                raise ValueError(f"Inconsistent nodegraphs. Cannot connect input "
                                 f"{mx_param.getNamePath()} to {val.getNamePath()}")

            mx_output_name = f'out_{node_name}'
            if nd_output:
                mx_output_name += f'_{nd_output.getName()}'

            mx_output = val_nodegraph.getOutput(mx_output_name)
            if not mx_output:
                mx_output = val_nodegraph.addOutput(mx_output_name, val.getType())
                mx_output.setNodeName(node_name)
                if nd_output:
                    mx_output.setType(nd_output.getType())
                    mx_output.setAttribute('output', nd_output.getName())

            mx_param.setAttribute('nodegraph', val_nodegraph.getName())
            mx_param.setAttribute('output', mx_output.getName())

    elif nd_type == 'filename':
        if isinstance(val, bpy.types.Image):
            mx_param.setValueString(str(cache_image_file(val)))
        else:
            mx_param.setValueString(str(val))

    else:
        mx_type = getattr(mx, title_str(nd_type), None)
        if mx_type:
            mx_param.setValue(mx_type(val))
        else:
            mx_param.setValue(val)


def is_value_equal(mx_val, val, nd_type):
    if nd_type in ('string', 'float', 'integer', 'boolean', 'angle'):
        return mx_val == val

    if nd_type == 'filename':
        val = "" if val is None else val
        return mx_val == val

    return tuple(mx_val) == tuple(val)


def is_shader_type(mx_type):
    return not (mx_type in ('string', 'float', 'integer', 'boolean', 'filename', 'angle') or
                mx_type.startswith('color') or
                mx_type.startswith('vector') or
                mx_type.endswith('array'))


def get_attr(mx_param, name, else_val=None):
    return mx_param.getAttribute(name) if mx_param.hasAttribute(name) else else_val


def parse_value(node, mx_val, mx_type, file_prefix=None):
    if mx_type in ('string', 'float', 'integer', 'boolean', 'filename', 'angle'):
        if file_prefix and mx_type == 'filename':
            mx_val = str((file_prefix / mx_val).resolve())

        if node.category in ('texture2d', 'texture3d') and mx_type == 'filename':
            file_path = Path(mx_val)
            if file_path.exists():
                image = bpy.data.images.get(file_path.name)
                if image and image.filepath_from_user() == str(file_path):
                    return image

                image = bpy.data.images.load(str(file_path))
                return image

            return None


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
    if mx_type in ('float', 'angle'):
        return float(val_str)
    if mx_type == 'boolean':
        return val_str == "true"
    if mx_type.endswith('array'):
        return val_str

    if mx_type.startswith('color') or mx_type.startswith('vector') or mx_type.startswith('matrix'):
        res = tuple(float(x) for x in val_str.split(','))
        return res[0] if first_only else res

    return val_str


def get_file_prefix(mx_node, file_path):
    file_prefix = file_path.parent
    n = mx_node
    while True:
        n = n.getParent()
        file_prefix /= n.getFilePrefix()
        if isinstance(n, mx.Document):
            break

    return file_prefix.resolve()


def get_nodegraph_by_node_path(doc, node_path, do_create=False):
    nodegraph_names = code_str(node_path).split('/')[:-1]
    mx_nodegraph = doc
    for nodegraph_name in nodegraph_names:
        next_mx_nodegraph = mx_nodegraph.getNodeGraph(nodegraph_name)
        if not next_mx_nodegraph:
            if do_create:
                next_mx_nodegraph = mx_nodegraph.addNodeGraph(nodegraph_name)
            else:
                return None

        mx_nodegraph = next_mx_nodegraph

    return mx_nodegraph


def get_node_name_by_node_path(node_path):
    return code_str(node_path.split('/')[-1])


def get_socket_color(mx_type):
    mx_type = mx_type.strip().lower()

    if not mx_type.startswith('displacement') and mx_type.endswith('shader') \
            or 'bsd' in mx_type or mx_type in ('material', 'edf', 'vdf'):
        return (0.39, 0.78, 0.39, 1.0)

    elif mx_type.startswith('color'):
        return (0.78, 0.78, 0.16, 1.0)

    elif mx_type in ('ior', 'integer', 'float', 'boolean', 'angle'):
        return (0.63, 0.63, 0.63, 1.0)

    elif mx_type.startswith('vector') or mx_type in ('normal', 'displacementshader', 'link', 'xyz'):
        return (0.39, 0.39, 0.78, 1.0)

    elif mx_type in ('string', 'filename'):
        return (0.44, 0.7, 1.0, 1.0)

    else:
        return (0.63, 0.63, 0.63, 1.0)
