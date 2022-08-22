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
import os
import MaterialX as mx
import bpy
import shutil

from pathlib import Path

from . import LIBS_DIR, title_str, code_str
from .image import cache_image_file

from . import logging
log = logging.Log('utils.mx')

MX_LIBS_FOLDER = "libraries"
MX_LIBS_DIR = LIBS_DIR / MX_LIBS_FOLDER

os.environ['MATERIALX_SEARCH_PATH'] = str(MX_LIBS_DIR)


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

            mx_output = val_nodegraph.getActiveOutput(mx_output_name)
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
            image_path = cache_image_file(val)
            if image_path:
                mx_param.setValueString(str(image_path))
        else:
            mx_param.setValueString(str(val))

    else:
        mx_type = getattr(mx, title_str(nd_type), None)
        if mx_type:
            val = mx_type(val)
        elif nd_type == 'float' and isinstance(val, tuple):
            val = val[0]

        mx_param.setValue(val)


def is_value_equal(mx_val, val, nd_type):
    if nd_type in ('string', 'float', 'integer', 'boolean', 'angle'):
        if nd_type == 'filename' and val is None:
            val = ""

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


def get_nodedef_inputs(nodedef, uniform=None):
    for nd_input in nodedef.getActiveInputs():
        if (uniform is True and nd_input.getAttribute('uniform') != 'true') or \
                (uniform is False and nd_input.getAttribute('uniform') == 'true'):
            continue

        yield nd_input


def get_file_prefix(mx_node, file_path):
    file_prefix = file_path.parent
    n = mx_node
    while True:
        n = n.getParent()
        file_prefix /= n.getFilePrefix()
        if isinstance(n, mx.Document):
            break

    return file_prefix.resolve()


def get_nodegraph_by_path(doc, ng_path, do_create=False):
    nodegraph_names = code_str(ng_path).split('/') if ng_path else ()
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


def get_nodegraph_by_node_path(doc, node_path, do_create=False):
    nodegraph_names = code_str(node_path).split('/')[:-1]
    return get_nodegraph_by_path(doc, '/'.join(nodegraph_names), do_create)


def get_node_name_by_node_path(node_path):
    return code_str(node_path.split('/')[-1])


def get_socket_color(mx_type):
    if mx_type.startswith('color'):
        return (0.78, 0.78, 0.16, 1.0)

    if mx_type in ('integer', 'float', 'boolean'):
        return (0.63, 0.63, 0.63, 1.0)

    if mx_type.startswith(('vector', 'matrix')) or mx_type in ('displacementshader'):
        return (0.39, 0.39, 0.78, 1.0)

    if mx_type in ('string', 'filename'):
        return (0.44, 0.7, 1.0, 1.0)

    if mx_type.endswith(('shader', 'material')) or mx_type in ('BSDF', 'EDF', 'VDF'):
        return (0.39, 0.78, 0.39, 1.0)

    return (0.63, 0.63, 0.63, 1.0)


def export_mx_to_file(doc, filepath, *, mx_node_tree=None, is_export_deps=False,
                      is_export_textures=False, texture_dir_name='textures',
                      is_clean_texture_folder=True, is_clean_deps_folders=True):
    root_dir = Path(filepath).parent

    if not os.path.isdir(root_dir):
        Path(root_dir).mkdir(parents=True, exist_ok=True)

    if is_export_deps and mx_node_tree:
        mx_libs_dir = root_dir / MX_LIBS_FOLDER
        if os.path.isdir(mx_libs_dir) and is_clean_deps_folders:
            shutil.rmtree(mx_libs_dir)

        # we need to export every deps only once
        unique_paths = set(node._file_path for node in mx_node_tree.nodes)

        for mtlx_path in unique_paths:
            # defining paths
            source_path = MX_LIBS_DIR.parent / mtlx_path
            full_dest_path = root_dir / mtlx_path
            rel_dest_path = full_dest_path.relative_to(root_dir / MX_LIBS_FOLDER)
            dest_path = root_dir / rel_dest_path

            Path(dest_path.parent).mkdir(parents=True, exist_ok=True)
            shutil.copy(source_path, dest_path)

            mx.prependXInclude(doc, str(rel_dest_path))

    if is_export_textures:
        texture_dir = root_dir / texture_dir_name
        if os.path.isdir(texture_dir) and is_clean_texture_folder:
            shutil.rmtree(texture_dir)

        image_paths = set()

        i = 0

        input_files = (v for v in doc.traverseTree() if isinstance(v, mx.Input) and v.getType() == 'filename')
        for mx_input in input_files:
            if not os.path.isdir(texture_dir):
                Path(texture_dir).mkdir(parents=True, exist_ok=True)

            mx_value = mx_input.getValue()
            if not mx_value:
                log.warn(f"Skipping wrong {mx_input.getType()} input value. Expected: path, got {mx_value}")
                continue

            source_path = Path(mx_value)
            if not os.path.isfile(source_path):
                log.warn("Image is missing", source_path)
                continue

            dest_path = texture_dir / source_path.name

            if source_path not in image_paths:
                image_paths.update([source_path])

                if os.path.isfile(dest_path):
                    i += 1
                    dest_path = texture_dir / f"{source_path.stem}_{i}{source_path.suffix}"
                else:
                    dest_path = texture_dir / f"{source_path.stem}{source_path.suffix}"

                shutil.copy(source_path, dest_path)
                log(f"Export file {source_path} to {dest_path}: completed successfuly")

            rel_dest_path = dest_path.relative_to(root_dir)
            mx_input.setValue(str(rel_dest_path), mx_input.getType())

    mx.writeToXmlFile(doc, filepath)
    log(f"Export MaterialX to {filepath}: completed successfuly")
