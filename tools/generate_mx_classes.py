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
import sys
from pathlib import Path
from collections import defaultdict


PYTHON_VERSION = f'{sys.version_info.major}.{sys.version_info.minor}'


repo_dir = Path(__file__).parent.parent
libs_dir = repo_dir / f"libs-{PYTHON_VERSION}"
mx_libs_dir = libs_dir / "libraries"


sys.path.append(str(libs_dir / "python"))
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


def generate_property_code(mx_param, category):
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
            if category in ("texture2d", "texture3d"):
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

        m = re.fullmatch(r'matrix(\d)(\d)', mx_type)
        if m:
            prop_type = "FloatVectorProperty"
            prop_attrs['subtype'] = 'MATRIX'
            prop_attrs['size'] = int(m[1]) * int(m[2])
            break

        m = re.fullmatch(r'color(\d)', mx_type)
        if m:
            prop_type = "FloatVectorProperty"
            prop_attrs['subtype'] = 'COLOR'
            prop_attrs['size'] = int(m[1])
            prop_attrs['soft_min'] = 0.0
            prop_attrs['soft_max'] = 1.0
            break

        m = re.fullmatch(r'vector(\d)', mx_type)
        if m:
            prop_type = "FloatVectorProperty"
            dim = int(m[1])
            prop_attrs['subtype'] = 'XYZ' if dim == 3 else 'NONE'
            prop_attrs['size'] = dim
            break

        m = re.fullmatch(r'(.+)array', mx_type)
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
            if prop_attr == 'default' and category in ("texture2d", "texture3d") and mx_type == 'filename':
                continue

            prop_attrs[prop_attr] = parse_value_str(
                mx_param.getAttribute(mx_attr), mx_type, first_only=mx_attr != 'value')

    prop_attr_strings = []
    for name, val in prop_attrs.items():
        val_str = f'"{val}"' if isinstance(val, str) else str(val)
        prop_attr_strings.append(f"{name}={val_str}")

    prop_attr_strings.append("update=MxNode.update_prop")

    if mx_type == 'filename' and category in ("texture2d", "texture3d"):
        prop_attr_strings.insert(0, "type=bpy.types.Image")

    return f"{prop_type}({', '.join(prop_attr_strings)})"


def get_attr(mx_param, name, else_val=""):
    return mx_param.getAttribute(name) if mx_param.hasAttribute(name) else else_val


def nodedef_data_type(nodedef):
    nd_name = nodedef.getName()
    node_name = nodedef.getNodeString()

    if nd_name.startswith('rpr_'):
        return nodedef.getOutputs()[0].getType()

    m = re.fullmatch(rf'ND_{node_name}_(.+)', nd_name)
    if m:
        return m[1]

    return nodedef.getOutputs()[0].getType()


def generate_data_type(nodedef):
    outputs = nodedef.getOutputs()
    if len(outputs) != 1:
        return f"{{'multitypes': {{'{nodedef.getName()}': None, 'nodedef_name': '{nodedef.getName()}'}}}}"

    return f"{{'{nodedef.getOutputs()[0].getType()}': {{'{nodedef.getName()}': None, 'nodedef_name': '{nodedef.getName()}'}}}}"


def input_prop_name(nd_type, name):
    return f'nd_{nd_type}_in_{name}'


def output_prop_name(nd_type, name):
    return f'nd_{nd_type}_out_{name}'


def folder_prop_name(name):
    return 'f_' + code_str(name.lower())


def get_mx_node_class_name(nodedef, prefix):
    return f"MxNode_{prefix}_{nodedef.getNodeString()}"


def generate_mx_node_class_code(nodedefs, prefix, category):
    nodedef = nodedefs[0]
    if not category:
        category = get_attr(nodedef, 'nodegroup', prefix)

    class_name = get_mx_node_class_name(nodedef, prefix)
    code_strings = []

    data_types = {}
    for nd in nodedefs:
        data_types[nodedef_data_type(nd)] = {'nd_name': nd.getName(), 'nd': None }

    code_strings.append(
f"""
class {class_name}(MxNode):
    _file_path = FILE_PATH
    _data_types = {data_types}
    
    bl_label = '{get_attr(nodedef, 'uiname', title_str(nodedef.getNodeString()))}'
    bl_idname = 'hdusd.{class_name}'
    bl_description = "{get_attr(nodedef, 'doc')}"
    
    category = '{category}'
""")

    ui_folders = []
    for mx_param in [*nodedef.getParameters(), *nodedef.getInputs()]:
        f = mx_param.getAttribute("uifolder")
        if f and f not in ui_folders:
            ui_folders.append(f)

    if len(ui_folders) > 2 or category in ("texture2d", "texture3d"):
        code_strings += ["    bl_width_default = 250", ""]

    if ui_folders:
        code_strings.append(f"    _ui_folders = {tuple(ui_folders)}")

    data_type_items = []
    index_default = 0
    for i, nd in enumerate(nodedefs):
        nd_type = nodedef_data_type(nd)

        data_type_items.append((nd_type, title_str(nd_type), title_str(nd_type)))
        if nd_type == 'color3':
            index_default = i

    code_strings += [
        f'    data_type: EnumProperty(name="Type", description="Input Data Type", '
        f"items={data_type_items}, default='{data_type_items[index_default][0]}', "
        f"update=MxNode.update_data_type)",
    ]

    for i, f in enumerate(ui_folders):
        if i == 0:
            code_strings.append("")

        code_strings.append(
            f'    {folder_prop_name(f)}: BoolProperty(name="{f}", '
            f'description="Enable {f}", default={i == 0}, update=MxNode.update_ui_folders)')

    for nd in nodedefs:
        nd_type = nodedef_data_type(nd)
        code_strings.append("")

        for input in nd.getInputs():
            prop_code = generate_property_code(input, category)
            code_strings.append(f"    {input_prop_name(nd_type, input.getName())}: {prop_code}")

        for output in nd.getOutputs():
            prop_code = generate_property_code(output, category)
            code_strings.append(f"    {output_prop_name(nd_type, output.getName())}: {prop_code}")

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
import bpy
from bpy.props import (
    EnumProperty,
    FloatProperty,
    IntProperty,
    BoolProperty,
    StringProperty,
    PointerProperty,
    FloatVectorProperty,
) 
from .base_node import MxNode


FILE_PATH = r"{file_path.relative_to(libs_dir)}"
""")

    doc = mx.createDocument()
    search_path = mx.FileSearchPath(str(mx_libs_dir))
    mx.readFromXmlFile(doc, str(file_path), searchPath=search_path)
    nodedefs = doc.getNodeDefs()

    # grouping node_def_classes by node and nodegroup
    node_def_classes_by_node = defaultdict(list)
    for nodedef in nodedefs:
        if nodedef.getSourceUri():
            continue

        if nodedef_data_type(nodedef) in IGNORE_NODEDEF_DATA_TYPE:
            print(f"Ignoring nodedef {nodedef.getName()}")
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
    gen_code_dir = repo_dir / "src/hdusd/mx_nodes/nodes"

    for f in gen_code_dir.glob("gen_*.py"):
        f.unlink()

    files = [
        ('PBR', "PBR", mx_libs_dir / "bxdf/standard_surface.mtlx"),
        ('USD', "USD", mx_libs_dir / "bxdf/usd_preview_surface.mtlx"),
        ('STD', None, mx_libs_dir / "stdlib/stdlib_defs.mtlx"),
        ('PBR', "PBR", mx_libs_dir / "pbrlib/pbrlib_defs.mtlx"),
        ('ALG', "Algorithm", mx_libs_dir / "alglib/alglib_defs.mtlx"),
    ]

    for prefix, category, file_path in files:

        module_name = f"gen_{file_path.name[:-len(file_path.suffix)]}"
        module_file = gen_code_dir / f"{module_name}.py"

        print(f"Generating {module_file} from {file_path}")
        module_code = generate_classes_code(file_path, prefix, category)
        module_file.write_text(module_code)


if __name__ == "__main__":
    main()
