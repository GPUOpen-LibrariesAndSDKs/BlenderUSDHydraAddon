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

from ...utils import prettify_string
from . import log


class MxNodeSocket(bpy.types.NodeSocket):
    bl_idname = 'hdusd.MxNodeSocket'
    bl_label = "MaterialX Node Socket"

    # TODO different type for draw color
    # socket_type: bpy.props.EnumProperty()

    # corresponding property name (if any) on node
    node_prop_name: bpy.props.StringProperty(default='')

    def draw(self, context, layout, node, text):
        # if not linked, we get custom property from the node
        # rather than use the default val like blender sockets
        # this allows custom property UI

        if self.is_linked:
            layout.label(text=self.name)
        else:
            layout.prop(node.prop, self.node_prop_name)

    def draw_color(self, context, node):
        # TODO get from type
        return (0.78, 0.78, 0.16, 1.0)


class MxNodedef(bpy.types.PropertyGroup):
    # holds the materialx nodedef object
    mx_nodedef: mx.NodeDef

    @staticmethod
    def new(mx_nodedef):
        annotations = {}
        for mx_param in mx_nodedef.getParameters():
            prop_name, prop_type, prop_attrs = MxNode.create_property(mx_param)
            annotations[prop_name] = prop_type, prop_attrs

        for mx_input in mx_nodedef.getInputs():
            prop_name, prop_type, prop_attrs = MxNode.create_property(mx_input)
            annotations['in_' + prop_name] = prop_type, prop_attrs

        for mx_output in mx_nodedef.getOutputs():
            prop_name, prop_type, prop_attrs = MxNode.create_property(mx_output)
            annotations['out_' + prop_name] = prop_type, prop_attrs

        data = {
            'mx_nodedef': mx_nodedef,
            '__annotations__': annotations
        }

        return type('Mx' + mx_nodedef.getName(), (MxNodedef,), data)


class MxNode(bpy.types.ShaderNode):
    """Base node from which all MaterialX nodes will be made"""
    bl_compatibility = {'HdUSD'}
    bl_idname = 'hdusd.MxNode'
    # bl_icon = 'MATERIAL'

    bl_label = ""
    bl_description = ""
    bl_width_default = 250

    def init(self, context):
        """generates inputs and outputs from ones specified in the mx_nodedef"""
        mx_nodedef = self.prop.mx_nodedef

        for mx_input in mx_nodedef.getInputs():
            self.create_input(mx_input)

        for mx_output in mx_nodedef.getOutputs():
            self.create_output(mx_output)

    def draw_buttons(self, context, layout):
        prop = self.prop
        for mx_param in prop.mx_nodedef.getParameters():
            layout.prop(prop, mx_param.getName())

    @property
    def prop(self):
        return getattr(self, self.variation)

    @classmethod
    def poll(cls, tree):
        return tree.bl_idname == 'hdusd.MxNodeTree'

    @staticmethod
    def import_from_mx(nt, mx_node: mx.Node):
        ''' creates a node from a Mx node spec
            sets the params and inputs based on spec '''

        # try:
        #     node_type = 'mx.' + mx_node.getCategory()
        #     blender_node = nt.nodes.new(node_type)
        #     blender_node.label = mx_node.getName()
        #     # get params from
        #     return blender_node
        # except:
        #     # TODO custom nodedefs in file
        #     return None
        pass

    @staticmethod
    def new(nodedef_types):
        mx_nodedef = nodedef_types[0].mx_nodedef
        node_name = mx_nodedef.getAttribute('node')

        annotations = {}
        var_items = []
        for nd_type in nodedef_types:
            name = nd_type.mx_nodedef.getName()[(4 + len(node_name)):]
            annotations[name] = (PointerProperty, {'type': nd_type})
            var_items.append((name, prettify_string(name), prettify_string(name)))

        annotations['variation'] = (EnumProperty, {
            'name': "Variation",
            'items': var_items,
            'default': var_items[0][0],
        })

        data = {
            'bl_label': prettify_string(mx_nodedef.getNodeString()),
            'bl_idname': MxNode.bl_idname + mx_nodedef.getName(),
            'bl_description': mx_nodedef.getAttribute('doc') if mx_nodedef.hasAttribute('doc')
                   else prettify_string(mx_nodedef.getName()),
            'nodegroup': mx_nodedef.getAttribute('nodegroup'),
            '__annotations__': annotations
        }

        return type('MxNode' + mx_nodedef.getName(), (MxNode,), data)

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
                    prop_attrs['items'] = tuple((it, prettify_string(it), prettify_string(it))
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
            else prettify_string(prop_name)
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
        input = self.inputs.new('hdusd.MxNodeSocket',
                                mx_input.getAttribute('uiname') if mx_input.hasAttribute('uiname')
                                else prettify_string(mx_input.getName()))
        input.node_prop_name = 'in_' + mx_input.getName()
        return input

    def create_output(self, mx_output):
        output = self.outputs.new('NodeSocketShader',
                                  mx_output.getAttribute('uiname') if mx_output.hasAttribute('uiname')
                                  else prettify_string(mx_output.getName()))
        return output


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
    nodedef_types = []
    for p in file_paths:
        doc = mx.createDocument()
        mx.readFromXmlFile(doc, str(p))
        mx_node_defs = doc.getNodeDefs()
        for mx_node_def in mx_node_defs:
            try:
                nodedef_types.append(MxNodedef.new(mx_node_def))
            except Exception as e:
                log.error(mx_node_def.getName(), e)

    node_types = [MxNode.new((nd_type,)) for nd_type in nodedef_types]

    return nodedef_types, node_types
