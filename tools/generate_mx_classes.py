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
import re
import sys
from pathlib import Path
from collections import defaultdict


repo_dir = Path(__file__).parent.parent
libs_dir = repo_dir / "libs"


sys.path.append(str(libs_dir / "materialx/python"))
import MaterialX as mx


def title_str(str):
    s = str.replace('_', ' ')
    return s[:1].upper() + s[1:]


def code_str(str):
    return str.replace(' ', '_').replace('.', '_')


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


def generate_property_code(mx_param, nodegroup):
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
            if nodegroup in ("texture2d", "texture3d"):
                prop_type = "PointerProperty"
                break

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
        if mx_type == 'angle':
            prop_type = "FloatProperty"
            prop_attrs['subtype'] = 'ANGLE'
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
        print("Unsupported mx_type", mx_type, mx_param, mx_param.getParent().getName())
        break

    for mx_attr, prop_attr in (('uimin', 'min'), ('uimax', 'max'),
                               ('uisoftmin', 'soft_min'), ('uisoftmax', 'soft_max'),
                               ('value', 'default')):
        if mx_param.hasAttribute(mx_attr):
            if prop_attr == 'default' and nodegroup in ("texture2d", "texture3d") and mx_type == 'filename':
                continue

            prop_attrs[prop_attr] = parse_value_str(
                mx_param.getAttribute(mx_attr), mx_type, first_only=mx_attr != 'value')

    prop_attr_strings = []
    for name, val in prop_attrs.items():
        val_str = f'"{val}"' if isinstance(val, str) else str(val)
        prop_attr_strings.append(f"{name}={val_str}")

    prop_attr_strings.append("update=MxNodeDef.update_prop")

    if mx_type == 'filename' and nodegroup in ("texture2d", "texture3d"):
        prop_attr_strings.insert(0, "type=bpy.types.Image")

    return f"{prop_type}({', '.join(prop_attr_strings)})"


def get_attr(mx_param, name, else_val=""):
    return mx_param.getAttribute(name) if mx_param.hasAttribute(name) else else_val


def nodedef_data_type(nodedef):
    # nodedef name consists: ND_{node_name}_{data_type} therefore:
    outputs = nodedef.getOutputs()
    if len(outputs) == 1:
        return nodedef.getOutputs()[0].getType()

    return "multitypes"


def param_prop_name(name):
    return 'p_' + name


def input_prop_name(name):
    return 'in_' + name


def output_prop_name(name):
    return 'out_' + name


def folder_prop_name(name):
    return 'f_' + code_str(name.lower())


def nodedef_prop_name(name):
    return 'nd_' + name


def get_mx_nodedef_class_name(nodedef, prefix):
    return f"MxNodeDef_{prefix}_{nodedef.getName()}"


def get_mx_node_class_name(nodedef, prefix):
    return f"MxNode_{prefix}_{nodedef.getNodeString()}"


def generate_mx_nodedef_class_code(nodedef: mx.NodeDef, prefix: str):
    code_strings = []
    code_strings.append(
f"""
class {get_mx_nodedef_class_name(nodedef, prefix)}(MxNodeDef):
    _file_path = FILE_PATH
    _nodedef_name = '{nodedef.getName()}'
    _node_name = '{nodedef.getNodeString()}'""")

    nodegroup = nodedef.getAttribute('nodegroup')

    for i, param in enumerate(nodedef.getParameters()):
        if i == 0:
            code_strings.append("")

        prop_code = generate_property_code(param, nodegroup)
        code_strings.append(f"    {param_prop_name(param.getName())}: {prop_code}")

    for i, input in enumerate(nodedef.getInputs()):
        if i == 0:
            code_strings.append("")

        prop_code = generate_property_code(input, nodegroup)
        code_strings.append(f"    {input_prop_name(input.getName())}: {prop_code}")

    for i, output in enumerate(nodedef.getOutputs()):
        if i == 0:
            code_strings.append("")

        prop_code = generate_property_code(output, nodegroup)
        code_strings.append(f"    {output_prop_name(output.getName())}: {prop_code}")

    code_strings.append("")
    return '\n'.join(code_strings)


def generate_mx_node_class_code(nodedefs, prefix, category):
    nodedef = nodedefs[0]
    if not category:
        category = get_attr(nodedef, 'nodegroup', prefix)

    class_name = get_mx_node_class_name(nodedef, prefix)
    code_strings = []
    code_strings.append(
f"""
class {class_name}(MxNode):
    bl_label = '{get_attr(nodedef, 'uiname', title_str(nodedef.getNodeString()))}'
    bl_idname = 'hdusd.{class_name}'
    bl_description = "{get_attr(nodedef, 'doc')}"
    
    category = '{category}'
    
    _data_types = {tuple(nodedef_data_type(nd) for nd in nodedefs)}
""")

    ui_folders = []
    for mx_param in [*nodedef.getParameters(), *nodedef.getInputs()]:
        f = mx_param.getAttribute("uifolder")
        if f and f not in ui_folders:
            ui_folders.append(f)

    if ui_folders:
        if len(ui_folders) > 2:
            code_strings.append("    bl_width_default = 250")
        code_strings.append(f"    _ui_folders = {tuple(ui_folders)}")

    data_type_items = []
    index_default = 0
    for i, nd in enumerate(nodedefs):
        nd_type = nodedef_data_type(nd)
        code_strings.append(
            f"    {nodedef_prop_name(nd_type)}: PointerProperty("
            f"type={get_mx_nodedef_class_name(nd, prefix)})")

        data_type_items.append((nd_type, title_str(nd_type), title_str(nd_type)))
        if nd_type == 'color3':
            index_default = i

    code_strings += [
        "",
        f'    data_type: EnumProperty(name="Type", description="Input Data Type", '
        f"items={data_type_items}, default='{data_type_items[index_default][0]}')",
    ]

    for i, f in enumerate(ui_folders):
        if i == 0:
            code_strings.append("")

        code_strings.append(
            f'    {folder_prop_name(f)}: BoolProperty(name="{f}", '
            f'description="Enable {f}", default={i == 0}, update=MxNode.ui_folders_update)')

    code_strings.append("")
    return '\n'.join(code_strings)


def generate_classes_code(file_path, prefix, category):
    IGNORE_NODEDEF_DATA_TYPE = ('matrix33', 'matrix44', 'matrix33FA', 'matrix44FA')

    code_strings = []
    code_strings.append(
f"""#**********************************************************************
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
from bpy.props import (
    EnumProperty,
    FloatProperty,
    IntProperty,
    BoolProperty,
    StringProperty,
    PointerProperty,
    FloatVectorProperty,
) 
from .base_node import MxNodeDef, MxNode

import bpy

FILE_PATH = r"{file_path.relative_to(libs_dir)}"
""")

    doc = mx.createDocument()
    mx.readFromXmlFile(doc, str(file_path))
    nodedefs = doc.getNodeDefs()
    nodedef_class_names = []
    for nodedef in nodedefs:
        if nodedef_data_type(nodedef) in IGNORE_NODEDEF_DATA_TYPE:
            continue

        code_strings.append(generate_mx_nodedef_class_code(nodedef, prefix))
        nodedef_class_names.append(get_mx_nodedef_class_name(nodedef, prefix))

    code_strings.append(f"""
mx_nodedef_classes = [{', '.join(nodedef_class_names)}]
""")

    # grouping node_def_classes by node and nodegroup
    node_def_classes_by_node = defaultdict(list)
    for nodedef in nodedefs:
        if nodedef_data_type(nodedef) in IGNORE_NODEDEF_DATA_TYPE:
            continue

        node_def_classes_by_node[(nodedef.getNodeString(), nodedef.getAttribute('nodegroup'))].\
            append(nodedef)

    # creating MxNode types
    mx_node_class_names = []
    for nodedefs_by_node in node_def_classes_by_node.values():
        code_strings.append(generate_mx_node_class_code(nodedefs_by_node, prefix, category))
        mx_node_class_names.append(get_mx_node_class_name(nodedefs_by_node[0], prefix))

    code_strings.append(f"""
mx_node_classes = [{', '.join(mx_node_class_names)}]
""")

    return '\n'.join(code_strings)


def main():
    mx_libs_dir = libs_dir / "materialx/libraries"
    gen_code_dir = repo_dir / "src/hdusd/mx_nodes/nodes"
    hdrpr_mat_dir = libs_dir / "hdrpr/materials"

    for f in gen_code_dir.glob("gen_*.py"):
        f.unlink()

    files = [
        ('PBR', "PBR", mx_libs_dir / "bxdf/standard_surface.mtlx"),
        ('USD', "USD", mx_libs_dir / "bxdf/usd_preview_surface.mtlx"),
        ('STD', None, mx_libs_dir / "stdlib/stdlib_defs.mtlx"),
        ('PBR', "PBR", mx_libs_dir / "pbrlib/pbrlib_defs.mtlx"),
    ]

    for f in (hdrpr_mat_dir / "Shaders").glob("rpr_*.mtlx"):
        files.append(('RPR', "RPR Shaders", f))

    for f in (hdrpr_mat_dir / "Utilities").glob("rpr_*.mtlx"):
        files.append(('RPR', "RPR Utilities", f))

    for f in (hdrpr_mat_dir / "Patterns").glob("rpr_*.mtlx"):
        files.append(('RPR', "RPR Patterns", f))

    for prefix, category, file_path in files:

        module_name = f"gen_{file_path.name[:-len(file_path.suffix)]}"
        module_file = gen_code_dir / f"{module_name}.py"

        print(f"Generating {module_file} from {file_path}")
        module_code = generate_classes_code(file_path, prefix, category)
        module_file.write_text(module_code)


if __name__ == "__main__":
    main()
