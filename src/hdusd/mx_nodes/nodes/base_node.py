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
import os
from collections import defaultdict

import MaterialX as mx

import bpy
from bpy.props import (
    StringProperty,
    IntProperty,
    FloatProperty,
    EnumProperty,
    FloatVectorProperty,
    IntVectorProperty,
    BoolProperty,
    PointerProperty,
)

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
            uiname = nd_input.getAttribute('uiname') if nd_input.hasAttribute('uiname') else \
                     title_str(nd_input.getName())
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
        uiname = mx_output.getAttribute('uiname') if mx_output.hasAttribute('uiname') else \
            title_str(mx_output.getName())
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
            mx.readFromXmlFile(doc, self.file_path)
            self._nodedef = doc.getNodeDef(self.nodedef_name)

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
        code_strings = [
            f"class {cls.get_class_name(nodedef, prefix)}(MxNodeDef):",
            f"    _file_path = FILE_PATH",
            f"    _nodedef_name = {nodedef.getName()}",
            "",
        ]
        for param in nodedef.getParameters():
            prop_code = mx_utils.get_property_code(param)
            code_strings.append(f"    {cls._param_prop_name(param.getName())} = {prop_code}")

        for input in nodedef.getInputs():
            prop_code = mx_utils.get_property_code(input)
            code_strings.append(f"    {cls._input_prop_name(input.getName())} = {prop_code}")

        for output in nodedef.getOutputs():
            prop_code = mx_utils.get_property_code(output)
            code_strings.append(f"    {cls._output_prop_name(output.getName())} = {prop_code}")

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
    bl_idname = 'hdusd.MxNode'
    # bl_icon = 'MATERIAL'

    bl_label = ""
    bl_description = ""
    bl_width_default = 200

    _nodedef_names = ()     # list of nodedefs
    _ui_folders = ()        # list of ui folders mentioned in nodedef
    data_type: EnumProperty
    category = ""


    @staticmethod
    def _folder_prop_name(name):
        return 'f_' + code_str(name)

    @staticmethod
    def _nodedef_prop_name(name):
        return 'nd_' + name

    @staticmethod
    def _nodedef_data_type(nd):
        # nodedef name consists: ND_{node_name}_{data_type} therefore:
        res = nd.getName()[(4 + len(nd.getNodeString())):]
        if not res:
            res = nd.getOutputs()[0].getType()

        return res

    @staticmethod
    def get_class_name(nodedef, prefix):
        return f"MxNode_{prefix}_{nodedef.getNodeString()}"

    @classmethod
    def generate_class_code(cls, nodedefs, prefix):
        nodedef = nodedefs[0]

        class_name = cls.get_class_name(nodedef, prefix)
        code_strings = [
            f"class {class_name}(MxNode):",
            f"    _file_path = FILE_PATH",

            f"    _nodedef_name = {nodedef.getName()}",
            "",
        ]
        for param in nodedef.getParameters():
            prop_code = mx_utils.get_property_code(param)
            code_strings.append(f"    {cls._param_prop_name(param.getName())} = {prop_code}")

        for input in nodedef.getInputs():
            prop_code = mx_utils.get_property_code(input)
            code_strings.append(f"    {cls._input_prop_name(input.getName())} = {prop_code}")

        for output in nodedef.getOutputs():
            prop_code = mx_utils.get_property_code(output)
            code_strings.append(f"    {cls._output_prop_name(output.getName())} = {prop_code}")

        code = os.linesep.join(code_strings)
        return name, code

    @staticmethod
    def new(node_def_classes, prefix):
        mx_nodedefs = tuple(NodeDef_cls.mx_nodedef for NodeDef_cls in node_def_classes)
        nd = mx_nodedefs[0]
        node_name = nd.getNodeString()

        annotations = {}
        data_type_items = []
        index_default = 0
        for i, NodeDef_cls in enumerate(node_def_classes):
            nd_type = MxNode._nodedef_data_type(NodeDef_cls.mx_nodedef)
            annotations[MxNode._nodedef_prop(nd_type)] = (PointerProperty, {'type': NodeDef_cls})
            data_type_items.append((nd_type, title_str(nd_type), title_str(nd_type)))
            if nd_type == 'color3':
                index_default = i

        annotations['data_type'] = (EnumProperty, {
            'name': "Type",
            'description': "Input Data Type",
            'items': data_type_items,
            'default': data_type_items[index_default][0],
        })

        ui_folders = []
        for mx_param in [*nd.getParameters(), *nd.getInputs()]:
            f = mx_param.getAttribute("uifolder")
            if f and f not in ui_folders:
                ui_folders.append(f)

        for i, f in enumerate(ui_folders):
            annotations[MxNode._folder_prop(f)] = BoolProperty, {
                'name': f,
                'description': f"Enable {f}",
                'default': i == 0,
                'update': MxNode.ui_folders_update,
            }

        data = {
            'bl_label': title_str(nd.getNodeString()),
            'bl_idname': f"{MxNode.bl_idname}_{prefix}_{node_name}",
            'bl_description': nd.getAttribute('doc') if nd.hasAttribute('doc')
            else title_str(nd.getName()),
            'bl_width_default': 250 if len(ui_folders) > 2 else 200,
            'mx_nodedefs': mx_nodedefs,
            'ui_folders': tuple(ui_folders),
            'category': nd.getAttribute('nodegroup') if nd.hasAttribute('nodegroup') else prefix,
            '__annotations__': annotations
        }

        return type(f'MxNode_{prefix}_{node_name}', (MxNode,), data)

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

    @staticmethod
    def create_property(mx_param):
        mx_type = mx_param.getType()
        prop_name = mx_param.getName()
        prop_attrs = {}

        while True:     # one way loop just for having break instead using nested 'if else'
            if mx_type == 'string':
                if mx_param.hasAttribute('enum'):
                    prop_type = EnumProperty
                    items = mx_utils.parse_value_str(mx_param.getAttribute('enum'), mx_type,
                                                     is_enum=True)
                    prop_attrs['items'] = tuple((it, title_str(it), title_str(it))
                                                for it in items)
                    break
                prop_type = StringProperty
                break
            if mx_type == 'filename':
                prop_type = StringProperty
                prop_attrs['subtype'] = 'FILE_PATH'
                break
            if mx_type == 'integer':
                prop_type = IntProperty
                break
            if mx_type == 'float':
                prop_type = FloatProperty
                break
            if mx_type == 'boolean':
                prop_type = BoolProperty
                break
            if mx_type in ('surfaceshader', 'displacementshader', 'volumeshader', 'lightshader',
                           'material', 'BSDF', 'VDF', 'EDF'):
                prop_type = StringProperty
                break

            m = re.fullmatch('matrix(\d)(\d)', mx_type)
            if m:
                prop_type = FloatVectorProperty
                prop_attrs['subtype'] = 'MATRIX'
                prop_attrs['size'] = int(m[1]) * int(m[2])
                break

            m = re.fullmatch('color(\d)', mx_type)
            if m:
                prop_type = FloatVectorProperty
                prop_attrs['subtype'] = 'COLOR'
                prop_attrs['size'] = int(m[1])
                prop_attrs['soft_min'] = 0.0
                prop_attrs['soft_max'] = 1.0
                break

            m = re.fullmatch('vector(\d)', mx_type)
            if m:
                prop_type = FloatVectorProperty
                dim = int(m[1])
                prop_attrs['subtype'] = 'XYZ' if dim == 3 else 'NONE'
                prop_attrs['size'] = dim
                break

            m = re.fullmatch('(.+)array', mx_type)
            if m:
                prop_type = StringProperty
                # TODO: Change to CollectionProperty
                break

            prop_type = StringProperty
            log.warn("Unsupported mx_type", mx_type, mx_param, mx_param.getParent().getName())
            break

        prop_attrs['name'] = mx_param.getAttribute('uiname') if mx_param.hasAttribute('uiname')\
            else title_str(prop_name)
        prop_attrs['description'] = mx_param.getAttribute('doc')

        for mx_attr, prop_attr in (('uimin', 'min'), ('uimax', 'max'),
                                   ('uisoftmin', 'soft_min'), ('uisoftmax', 'soft_max'),
                                   ('value', 'default')):
            if mx_param.hasAttribute(mx_attr):
                prop_attrs[prop_attr] = mx_utils.parse_value_str(
                    mx_param.getAttribute(mx_attr), mx_type, first_only=mx_attr != 'value')

        return prop_name, prop_type, prop_attrs

    def create_input(self, mx_input):
        return self.inputs.new(MxNodeInputSocket.bl_idname, mx_input.getName())

    def create_output(self, mx_output):
        return self.outputs.new(MxNodeOutputSocket.bl_idname, mx_output.getName())


def create_node_types(file_paths):
    IGNORE_NODEDEF_DATA_TYPE = ('matrix33', 'matrix44')

    all_node_def_classes = []
    all_mx_node_classes = []

    for prefix, file_path in file_paths:
        doc = mx.createDocument()
        mx.readFromXmlFile(doc, str(file_path))
        mx_nodedefs = doc.getNodeDefs()
        node_def_classes = []
        for mx_nodedef in mx_nodedefs:
            if MxNode._nodedef_data_type(mx_nodedef) in IGNORE_NODEDEF_DATA_TYPE:
                continue

            node_def_classes.append(MxNodeDef.new(mx_nodedef, prefix))

        # grouping node_def_classes by node and nodegroup
        node_def_classes_by_node = defaultdict(list)
        for NodeDef_cls in node_def_classes:
            nd = NodeDef_cls.mx_nodedef
            node_def_classes_by_node[(nd.getNodeString(), nd.getAttribute('nodegroup'))].\
                append(NodeDef_cls)

        # creating MxNode types
        mx_node_classes = []
        for _, nd_types in node_def_classes_by_node.items():
            mx_node_classes.append(MxNode.new(nd_types, prefix))

        all_node_def_classes.extend(node_def_classes)
        all_mx_node_classes.extend(mx_node_classes)

    return all_node_def_classes, all_mx_node_classes
