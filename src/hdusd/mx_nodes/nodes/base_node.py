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
from . import log


def is_shader_type(mx_type):
    return not (mx_type in ('string', 'float', 'integer', 'boolean', 'filename') or
                mx_type.startswith('color') or
                mx_type.startswith('vector') or
                mx_type.endswith('array'))


class MxNodeInputSocket(bpy.types.NodeSocket):
    bl_idname = 'hdusd.MxNodeInputSocket'
    bl_label = "MX Input Socket"

    @staticmethod
    def get_color(type_name):
        return (0.78, 0.78, 0.16, 1.0) if is_shader_type(type_name) else (0.16, 0.78, 0.16, 1.0)

    def draw(self, context, layout, node, text):
        mx_input = node.prop.mx_nodedef.getInput(self.name)
        nd_type = mx_input.getType()

        if self.is_linked or is_shader_type(nd_type):
            uiname = mx_input.getAttribute('uiname') if mx_input.hasAttribute('uiname') else \
                     title_str(mx_input.getName())
            uitype = title_str(nd_type)
            layout.label(text=uiname if uiname == uitype else f"{uiname}: {uitype}")
        else:
            layout.prop(node.prop, MxNode._input_prop(self.name))

    def draw_color(self, context, node):
        return self.get_color(node.prop.mx_nodedef.getInput(self.name).getType())


class MxNodeOutputSocket(bpy.types.NodeSocket):
    bl_idname = 'hdusd.MxNodeOutputSocket'
    bl_label = "MX Output Socket"

    def draw(self, context, layout, node, text):
        mx_output = node.prop.mx_nodedef.getOutput(self.name)
        layout.label(text=title_str(mx_output.getType()))

    def draw_color(self, context, node):
        return MxNodeInputSocket.get_color(node.prop.mx_nodedef.getOutput(self.name).getType())


class MxNode(bpy.types.ShaderNode):
    """Base node from which all MaterialX nodes will be made"""
    bl_compatibility = {'HdUSD'}
    bl_idname = 'hdusd.MxNode'
    # bl_icon = 'MATERIAL'

    bl_label = ""
    bl_description = ""
    bl_width_default = 250

    mx_nodedefs = ()    # list of nodedefs
    ui_folders = ()     # list of ui folders mentioned in nodedef
    data_type: EnumProperty

    @staticmethod
    def _param_prop(name):
        return 'p_' + name

    @staticmethod
    def _input_prop(name):
        return 'in_' + name

    @staticmethod
    def _output_prop(name):
        return 'out_' + name

    @staticmethod
    def _folder_prop(name):
        return 'f_' + code_str(name)

    @staticmethod
    def _nodedef_prop(name):
        return 'nd_' + name

    @staticmethod
    def _nodedef_data_type(nd):
        # nodedef name consists: ND_{node_name}_{data_type} therefore:
        return nd.getName()[(4 + len(nd.getNodeString())):]

    class NodeDef(bpy.types.PropertyGroup):
        mx_nodedef: mx.NodeDef  # holds the materialx nodedef object

        @staticmethod
        def new(mx_nodedef, prefix):
            annotations = {}
            for mx_param in mx_nodedef.getParameters():
                prop_name, prop_type, prop_attrs = MxNode.create_property(mx_param)
                annotations[MxNode._param_prop(prop_name)] = prop_type, prop_attrs

            for mx_input in mx_nodedef.getInputs():
                prop_name, prop_type, prop_attrs = MxNode.create_property(mx_input)
                annotations[MxNode._input_prop(prop_name)] = prop_type, prop_attrs

            for mx_output in mx_nodedef.getOutputs():
                prop_name, prop_type, prop_attrs = MxNode.create_property(mx_output)
                annotations[MxNode._output_prop(prop_name)] = prop_type, prop_attrs

            data = {
                'mx_nodedef': mx_nodedef,
                '__annotations__': annotations
            }

            return type(f'MxNodeDef_{prefix}_{mx_nodedef.getName()}', (MxNode.NodeDef,), data)

    def init(self, context):
        """generates inputs and outputs from ones specified in the mx_nodedef"""
        nd = self.prop.mx_nodedef

        for mx_input in nd.getInputs():
            self.create_input(mx_input)

        for mx_output in nd.getOutputs():
            self.create_output(mx_output)

        if self.ui_folders:
            self.ui_folders_update(context)

    def draw_buttons(self, context, layout):
        if len(self.mx_nodedefs) > 1:
            layout.prop(self, 'data_type')

        prop = self.prop

        if self.ui_folders:
            col = layout.column(align=True)
            r = None
            for i, f in enumerate(self.ui_folders):
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
        def set_value(param, val, nd_type):
            if isinstance(val, mx.Node):
                param.setNodeName(val.getName())
            elif nd_type == 'filename':
                param.setValueString(val)
            else:
                mx_type = getattr(mx, title_str(nd_type), None)
                if mx_type:
                    param.setValue(mx_type(val))
                else:
                    param.setValue(val)

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
            if is_shader_type(nd_input.getType()) and not isinstance(val, mx.Node):
                continue

            input = node.addInput(nd_input.getName(), nd_input.getType())
            set_value(input, val, nd_input.getType())

        for nd_param in nodedef.getParameters():
            val = self.get_param_value(nd_param.getName())
            param = node.addParameter(nd_param.getName(), nd_param.getType())
            set_value(param, val, nd_param.getType())

        return node

    def _compute_node(self, node, out_key, **kwargs):
        if not isinstance(node, MxNode):
            log.warn("Ignoring unsupported node", node)
            return None

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
        return getattr(self.prop, self._input_prop(self.inputs[in_key].identifier))

    def get_param_value(self, name):
        return getattr(self.prop, self._param_prop(name))

    def get_nodedef_input(self, in_key: [str, int]):
        return self.prop.mx_nodedef.getInput(self.inputs[in_key].identifier)

    def get_nodedef_output(self, out_key: [str, int]):
        return self.prop.mx_nodedef.getOutput(self.outputs[out_key].identifier)

    @property
    def prop(self):
        return getattr(self, self._nodedef_prop(self.data_type))

    @classmethod
    def poll(cls, tree):
        return tree.bl_idname == 'hdusd.MxNodeTree'

    @staticmethod
    def new(node_def_classes, prefix):
        mx_nodedefs = tuple(NodeDef_cls.mx_nodedef for NodeDef_cls in node_def_classes)
        nd = mx_nodedefs[0]
        node_name = nd.getNodeString()

        annotations = {}
        data_type_items = []
        index_default = 0
        for i, NodeDef_cls in enumerate(node_def_classes):
            nd_name = NodeDef_cls.mx_nodedef.getName()
            data_type = MxNode._nodedef_data_type(NodeDef_cls.mx_nodedef)
            annotations[MxNode._nodedef_prop(nd_name)] = (PointerProperty, {'type': NodeDef_cls})
            data_type_items.append((nd_name, title_str(data_type), title_str(data_type)))
            if data_type == 'color3':
                index_default = i

        annotations['data_type'] = (EnumProperty, {
            'name': "Data Type",
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
            '__annotations__': annotations
        }

        return type(f'MxNode_{prefix}_{node_name}', (MxNode,), data)

    def ui_folders_update(self, context):
        for i, mx_input in enumerate(self.prop.mx_nodedef.getInputs()):
            f = mx_input.getAttribute('uifolder')
            if f:
                self.inputs[i].hide = not getattr(self, self._folder_prop(f))

    @staticmethod
    def create_property(mx_param):
        mx_type = mx_param.getType()
        prop_name = mx_param.getName()
        prop_attrs = {}

        while True:     # one way loop just for having break instead using nested 'if else'
            if mx_type == 'string':
                if mx_param.hasAttribute('enum'):
                    prop_type = EnumProperty
                    items = parse_val(prop_type, mx_param.getAttribute('enum'))
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

        if mx_param.hasAttribute('uimin'):
            prop_attrs['min'] = parse_val(prop_type, mx_param.getAttribute('uimin'), True)
        if mx_param.hasAttribute('uimax'):
            prop_attrs['max'] = parse_val(prop_type, mx_param.getAttribute('uimax'), True)
        if mx_param.hasAttribute('uisoftmin'):
            prop_attrs['soft_min'] = parse_val(prop_type, mx_param.getAttribute('uisoftmin'), True)
        if mx_param.hasAttribute('uisoftmax'):
            prop_attrs['soft_max'] = parse_val(prop_type, mx_param.getAttribute('uisoftmax'), True)

        if mx_param.hasAttribute('value'):
            prop_attrs['default'] = parse_val(prop_type, mx_param.getAttribute('value'),
                                              prop_type == EnumProperty)

        return prop_name, prop_type, prop_attrs

    def create_input(self, mx_input):
        return self.inputs.new(MxNodeInputSocket.bl_idname, mx_input.getName())

    def create_output(self, mx_output):
        return self.outputs.new(MxNodeOutputSocket.bl_idname, mx_output.getName())


def parse_val(prop_type, val, first_only=False):
    if prop_type == StringProperty:
        return val
    if prop_type == IntProperty:
        return int(val)
    if prop_type == FloatProperty:
        return float(val)
    if prop_type == BoolProperty:
        return val == "true"
    if prop_type == FloatVectorProperty:
        res = tuple(float(x) for x in val.split(','))
        if first_only:
            return res[0]
        return res
    if prop_type == EnumProperty:
        res = tuple(x.strip() for x in val.split(','))
        if first_only:
            return res[0]
        return res


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

            node_def_classes.append(MxNode.NodeDef.new(mx_nodedef, prefix))

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
