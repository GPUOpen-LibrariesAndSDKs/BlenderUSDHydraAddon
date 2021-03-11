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
from collections import defaultdict
from pathlib import Path
import importlib

import MaterialX as mx

import bpy

from ...utils import title_str, code_str
from ...utils import mx as mx_utils
from . import log


class MxNodeInputSocket(bpy.types.NodeSocket):
    bl_idname = 'hdusd.MxNodeInputSocket'
    bl_label = "MX Input Socket"

    @staticmethod
    def get_color(type_name):
        return (0.78, 0.78, 0.16, 1.0) if mx_utils.is_shader_type(type_name) else \
               (0.16, 0.78, 0.16, 1.0)

    def draw(self, context, layout, node, text):
        nd = node.prop.mx_nodedef
        nd_input = nd.getInput(self.name)
        nd_type = nd_input.getType()

        if self.is_linked or mx_utils.is_shader_type(nd_type) or nd_input.getValue() is None:
            uiname = mx_utils.get_attr(nd_input, 'uiname', title_str(nd_input.getName()))
            uitype = title_str(nd_type)
            if uiname.lower() == uitype.lower():
                layout.label(text=uitype)
            else:
                layout.label(text=f"{uiname}: {uitype}")
        else:
            layout.prop(node.prop, MxNode._input_prop(self.name))

    def draw_color(self, context, node):
        return self.get_color(node.prop.mx_nodedef.getInput(self.name).getType())


class MxNodeOutputSocket(bpy.types.NodeSocket):
    bl_idname = 'hdusd.MxNodeOutputSocket'
    bl_label = "MX Output Socket"

    def draw(self, context, layout, node, text):
        nd = node.prop.mx_nodedef
        mx_output = nd.getOutput(self.name)
        uiname = mx_utils.get_attr(mx_output, 'uiname', title_str(mx_output.getName()))
        uitype = title_str(mx_output.getType())
        if uiname.lower() == uitype.lower() or len(nd.getOutputs()) == 1:
            layout.label(text=uitype)
        else:
            layout.label(text=f"{uiname}: {uitype}")

    def draw_color(self, context, node):
        return MxNodeInputSocket.get_color(node.prop.mx_nodedef.getOutput(self.name).getType())


class MxNodeDef(bpy.types.PropertyGroup):
    _file_path: str
    _nodedef_name: str

    _nodedef: mx.NodeDef

    @property
    def nodedef(self):
        if not self._mx_nodedef:
            doc = mx.createDocument()
            mx.readFromXmlFile(doc, self._file_path)
            self._nodedef = doc.getNodeDef(self._nodedef_name)

        return self._nodedef

    @staticmethod
    def _param_prop_name(name):
        return 'p_' + name

    @staticmethod
    def _input_prop_name(name):
        return 'in_' + name

    @staticmethod
    def _output_prop_name(name):
        return 'out_' + name

    @staticmethod
    def get_class_name(nodedef, prefix):
        return f"MxNodeDef_{prefix}_{nodedef.getName()}"

    @classmethod
    def generate_class_code(cls, nodedef: mx.NodeDef, prefix: str):
        code_strings = []
        code_strings.append(
f"""
class {cls.get_class_name(nodedef, prefix)}(MxNodeDef):
    _file_path = FILE_PATH
    _nodedef_name = '{nodedef.getName()}'
""")
        for param in nodedef.getParameters():
            prop_code = mx_utils.get_property_code(param)
            code_strings.append(f"    {cls._param_prop_name(param.getName())}: {prop_code}")

        code_strings.append("")
        for input in nodedef.getInputs():
            prop_code = mx_utils.get_property_code(input)
            code_strings.append(f"    {cls._input_prop_name(input.getName())}: {prop_code}")

        code_strings.append("")
        for output in nodedef.getOutputs():
            prop_code = mx_utils.get_property_code(output)
            code_strings.append(f"    {cls._output_prop_name(output.getName())}: {prop_code}")

        return os.linesep.join(code_strings)

    def get_input(self, name):
        return getattr(self, self._input_prop_name(name))

    def set_input(self, name, value):
        setattr(self, self._input_prop_name(name), value)

    def get_param(self, name):
        return getattr(self, self._param_prop_name(name))

    def set_param(self, name, value):
        setattr(self, self._param_prop_name(name), value)

    def get_nodedef_input(self, name):
        return self.nodedef.getInput(name)

    def get_nodedef_output(self, name):
        return self.nodedef.getOutput(name)


class MxNode(bpy.types.ShaderNode):
    """Base node from which all MaterialX nodes will be made"""
    bl_compatibility = {'HdUSD'}
    bl_idname = 'hdusd.'
    # bl_icon = 'MATERIAL'

    bl_label = ""
    bl_description = ""
    bl_width_default = 200

    _data_types = ()    # list of available types from nodedefs
    _ui_folders = ()    # list of ui folders mentioned in nodedef
    category = ""
    data_type = None

    @staticmethod
    def _folder_prop_name(name):
        return 'f_' + code_str(name)

    @staticmethod
    def _nodedef_prop_name(name):
        return 'nd_' + name

    @staticmethod
    def get_class_name(nodedef, prefix):
        return f"MxNode_{prefix}_{nodedef.getNodeString()}"

    @classmethod
    def generate_class_code(cls, nodedefs, prefix):
        nodedef = nodedefs[0]

        class_name = cls.get_class_name(nodedef, prefix)
        code_strings = []
        code_strings.append(
f"""
class {class_name}(MxNode):
    bl_label = '{title_str(nodedef.getNodeString())}'
    bl_idname = '{MxNode.bl_idname}{class_name}'
    bl_description = '{mx_utils.get_attr(nodedef, 'doc', title_str(nodedef.getName()))}'

    catergory = '{mx_utils.get_attr(nodedef, 'nodegroup', prefix)}'

    _data_types = {tuple(mx_utils.nodedef_data_type(nd) for nd in nodedefs)}
""")

        ui_folders = []
        for mx_param in [*nodedef.getParameters(), *nodedef.getInputs()]:
            f = mx_param.getAttribute("uifolder")
            if f and f not in ui_folders:
                ui_folders.append(f)

        if ui_folders:
            if len(ui_folders) > 2:
                code_strings.append("    bl_width_default = 250")
            code_strings.append(f"    _ua_folders = {tuple(ui_folders)}")

        data_type_items = []
        index_default = 0
        for i, nd in enumerate(nodedefs):
            nd_type = mx_utils.nodedef_data_type(nd)
            code_strings.append(
                f"    {cls._nodedef_prop_name(nd_type)}: PointerProperty("
                f"type={MxNodeDef.get_class_name(nd, prefix)})")

            data_type_items.append((nd_type, title_str(nd_type), title_str(nd_type)))
            if nd_type == 'color3':
                index_default = i

        code_strings += [
            "",
            f"    data_type: EnumProperty(name='Type', description='Input Data Type', "
            f"items={data_type_items}, default='{data_type_items[index_default][0]}')",
            "",
        ]

        for i, f in enumerate(ui_folders):
            code_strings.append(
                f"    {cls._folder_prop_name(f)}: BoolProperty(name='{f}', "
                f"description='Enable {f}', default={i == 0}, update=MxNode.ui_folders_update)")

        return os.linesep.join(code_strings)

    def init(self, context):
        """generates inputs and outputs from ones specified in the mx_nodedef"""
        nd = self.prop.mx_nodedef

        for mx_input in nd.getInputs():
            self.create_input(mx_input)

        for mx_output in nd.getOutputs():
            self.create_output(mx_output)

        if self._ui_folders:
            self.ui_folders_update(context)

    def draw_buttons(self, context, layout):
        if len(self.mx_nodedefs) > 1:
            layout.prop(self, 'data_type')

        prop = self.prop

        if self._ui_folders:
            col = layout.column(align=True)
            r = None
            for i, f in enumerate(self._ui_folders):
                if i % 3 == 0:  # putting 3 buttons per row
                    r = col.row(align=True)
                r.prop(self, self._folder_prop(f), toggle=True)

        for mx_param in prop.mx_nodedef.getParameters():
            f = mx_param.getAttribute('uifolder')
            if f and not getattr(self, self._folder_prop(f)):
                continue

            layout.prop(prop, self._param_prop(mx_param.getName()))

    # COMPUTE FUNCTION
    def compute(self, out_key, **kwargs):
        log("compute", self, out_key)

        doc = kwargs['doc']
        nodedef = self.prop.mx_nodedef
        nd_output = self.get_nodedef_output(out_key)

        values = []
        for in_key in range(len(self.inputs)):
            values.append(self.get_input_value(in_key, **kwargs))

        node = doc.addNode(nodedef.getNodeString(), code_str(self.name), nd_output.getType())
        for in_key, val in enumerate(values):
            nd_input = self.get_nodedef_input(in_key)
            nd_type = nd_input.getType()
            if not isinstance(val, mx.Node):
                if mx_utils.is_shader_type(nd_type):
                    continue

                nd_val = nd_input.getValue()
                if nd_val is None or mx_utils.is_value_equal(nd_val, val, nd_type):
                    continue

            input = node.addInput(nd_input.getName(), nd_type)
            mx_utils.set_param_value(input, val, nd_type)

        for nd_param in nodedef.getParameters():
            val = self.get_param_value(nd_param.getName())
            nd_type = nd_param.getType()
            if mx_utils.is_value_equal(nd_param.getValue(), val, nd_type):
                continue

            param = node.addParameter(nd_param.getName(), nd_type)
            mx_utils.set_param_value(param, val, nd_type)

        return node

    def _compute_node(self, node, out_key, **kwargs):
        doc = kwargs['doc']
        mx_node = doc.getNode(code_str(node.name))
        if mx_node:
            return mx_node

        return node.compute(out_key, **kwargs)

    def get_input_link(self, in_key: [str, int], **kwargs):
        """Returns linked parsed node or None if nothing is linked or not link is not valid"""

        socket_in = self.inputs[in_key]
        if not socket_in.links:
            return None

        link = socket_in.links[0]
        if not link.is_valid:
            log.error("Invalid link found", link, socket_in, self)

        return self._compute_node(link.from_node, link.from_socket.name, **kwargs)

    def get_input_value(self, in_key: [str, int], **kwargs):
        node = self.get_input_link(in_key, **kwargs)
        if node:
            return node

        return self.get_input_default(in_key)

    def get_input_default(self, in_key: [str, int]):
        return self.prop.get_input(self.inputs[in_key].identifier)

    def get_param_value(self, name):
        return self.prop.get_param(name)

    def get_nodedef_input(self, in_key: [str, int]):
        return self.prop.get_nodedef_input(self.inputs[in_key].identifier)

    def get_nodedef_output(self, out_key: [str, int]):
        return self.prop.get_nodedef_output(self.outputs[out_key].identifier)

    def set_input_default(self, in_key, value):
        self.prop.set_input(self.inputs[in_key].identifier, value)

    def set_param_value(self, name, value):
        self.prop.set_param(name, value)

    @property
    def prop(self):
        return getattr(self, self._nodedef_prop(self.data_type))

    @classmethod
    def poll(cls, tree):
        return tree.bl_idname == 'hdusd.MxNodeTree'

    def ui_folders_update(self, context):
        for i, mx_input in enumerate(self.prop.mx_nodedef.getInputs()):
            f = mx_input.getAttribute('uifolder')
            if f:
                self.inputs[i].hide = not getattr(self, self._folder_prop(f))

    def ui_folders_check(self):
        if not self._ui_folders:
            return

        for f in self._ui_folders:
            setattr(self, self._folder_prop(f), False)

        for in_key, mx_input in enumerate(self.prop.mx_nodedef.getInputs()):
            f = mx_input.getAttribute('uifolder')
            if not f:
                continue

            if self.inputs[in_key].links:
                setattr(self, self._folder_prop(f), True)
                continue

            nd_input = self.get_nodedef_input(in_key)
            val = self.get_input_default(in_key)
            nd_val = nd_input.getValue()
            if nd_val is None or mx_utils.is_value_equal(nd_val, val, nd_input.getType()):
                continue

            setattr(self, self._folder_prop(f), True)

        self.ui_folders_update(None)

    def create_input(self, mx_input):
        return self.inputs.new(MxNodeInputSocket.bl_idname, mx_input.getName())

    def create_output(self, mx_output):
        return self.outputs.new(MxNodeOutputSocket.bl_idname, mx_output.getName())


def generate_classes_code(file_path, prefix):
    IGNORE_NODEDEF_DATA_TYPE = ('matrix33', 'matrix44')

    code_strings = []
    code_strings.append(
f"""
# This file was generated from {file_path}

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


FILE_PATH = '{file_path}'

""")

    doc = mx.createDocument()
    mx.readFromXmlFile(doc, str(file_path))
    nodedefs = doc.getNodeDefs()
    node_def_class_names = []
    for nodedef in nodedefs:
        if mx_utils.nodedef_data_type(nodedef) in IGNORE_NODEDEF_DATA_TYPE:
            continue

        code_strings.append(MxNodeDef.generate_class_code(nodedef, prefix))
        code_strings.append("")
        node_def_class_names.append(MxNodeDef.get_class_name(nodedef, prefix))

    code_strings.append(f"node_def_class_names = {tuple(node_def_class_names)}")

    # grouping node_def_classes by node and nodegroup
    node_def_classes_by_node = defaultdict(list)
    for nodedef in nodedefs:
        node_def_classes_by_node[(nodedef.getNodeString(), nodedef.getAttribute('nodegroup'))].\
            append(nodedef)

    # creating MxNode types
    mx_node_class_names = []
    for nodedefs_by_node in node_def_classes_by_node.values():
        code_strings.append(MxNode.generate_class_code(nodedefs_by_node, prefix))
        code_strings.append("")
        mx_node_class_names.append(MxNode.get_class_name(nodedefs_by_node[0], prefix))

    code_strings.append(f"mx_node_class_names = {tuple(mx_node_class_names)}")

    return os.linesep.join(code_strings)


def create_node_types(prefix_file_paths):
    all_node_def_classes = []
    all_mx_node_classes = []

    for prefix, file_path in prefix_file_paths:
        module_name = f"gen_{file_path.name[:-len(file_path.suffix)]}"
        module_file = Path(__file__).parent / f"{module_name}.py"
        if True: #not module_file.exists():
            module_code = generate_classes_code(file_path, prefix)
            module_file.write_text(module_code)

        module = importlib.import_module(f'.{module_name}', 'hdusd.mx_nodes.nodes')

        for name in module.node_def_class_names:
            all_node_def_classes.append(getattr(module, name))

        for name in module.mx_node_class_names:
            all_mx_node_classes.append(getattr(module, name))

    return all_node_def_classes, all_mx_node_classes
