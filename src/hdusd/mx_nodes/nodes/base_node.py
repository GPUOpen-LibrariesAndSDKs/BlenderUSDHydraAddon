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
)

from . import log


def prettify_string(str):
    return str.replace('_', ' ').title()


class MxNodeSocket(bpy.types.NodeSocket):
    bl_idname = 'hdusd.MxNodeSocket'
    bl_label = "MaterialX Node Socket"

    # TODO different type for draw color
    # socket_type: bpy.props.EnumProperty()

    # corresponding property name (if any) on node
    property_name: bpy.props.StringProperty(default='')

    def draw(self, context, layout, node, text):
        # if not linked, we get custom property from the node
        # rather than use the default val like blender sockets
        # this allows custom property UI
        if self.is_linked or self.property_name == '':
            layout.label(text=self.name)
        else:
            layout.prop(node, self.property_name, text=self.name)

    def draw_color(self, context, node):
        # TODO get from type
        return (0.78, 0.78, 0.16, 1.0)


class MxNode(bpy.types.ShaderNode):
    """Base node from which all MaterialX nodes will be made"""
    bl_compatibility = {'HdUSD'}
    bl_idname = 'MX_'
    # bl_icon = 'MATERIAL'

    bl_label = ""
    bl_description = ""

    # holds the materialx nodedef object
    mx_nodedef: mx.NodeDef

    @property
    def nodegroup(self):
        return ""

    def init(self, context):
        """generates inputs and outputs from ones specified in the mx_nodedef"""

        for mx_input in self.mx_nodedef.getInputs():
            name = mx_input.getName()
            input = self.inputs.new(name=prettify_string(name), type='hdusd.MxNodeSocket')
            if hasattr(self, name.lower()):
                input.property_name = name.lower()

        for output in self.mx_nodedef.getOutputs():
            name = output.getName()
            self.outputs.new(name=prettify_string(name), type='hdusd.MxNodeSocket')

    def draw_buttons(self, context, layout):
        for mx_param in self.mx_nodedef.getParameters():
            layout.prop(self, mx_param.getName())

    @classmethod
    def poll(cls, tree):
        return tree.bl_idname == 'hdusd.MxNodeTree'

    @staticmethod
    def import_from_mx(nt, mx_node: mx.Node):
        ''' creates a node from a Mx node spec
            sets the params and inputs based on spec '''

        try:
            node_type = 'mx.' + mx_node.getCategory()
            blender_node = nt.nodes.new(node_type)
            blender_node.label = mx_node.getName()
            # get params from
            return blender_node
        except:
            # TODO custom nodedefs in file
            return None

    @staticmethod
    def create_node_type(mx_nodedef):
        annotations = {}
        for mx_param in mx_nodedef.getParameters():
            prop_name, prop_type, prop_attrs = MxNode.create_property(mx_param)
            annotations[prop_name] = prop_type, prop_attrs

        # for mx_input in mx_nodedef.getInputs():
        #     created_property = get_param(mx_input)
        #     if created_property is not None:
        #         annotations[mx_input.getName()] = created_property

        data = {
            'bl_label': prettify_string(mx_nodedef.getNodeString()),
            'bl_idname': "hdusd.MX_" + mx_nodedef.getNodeString(),
            'mx_nodedef': mx_nodedef,
            '__annotations__': annotations
        }

        node_type = type('MX_' + mx_nodedef.getNodeString(), (MxNode,), data)
        return node_type

    @staticmethod
    def create_property(mx_param):
        mx_type = mx_param.getType()
        prop_name = mx_param.getName()
        prop_attrs = {}

        while True:     # one way loop just for having break instead using nested 'if else'
            if mx_type == 'string':
                if mx_param.hasAttribute('enum'):
                    prop_type = EnumProperty
                    prop_attrs['items'] = parse_val(prop_type, mx_param.getAttribute('enum'))
                    break
                prop_type = StringProperty
                break
            if mx_type == 'filename':
                prop_type = StringProperty
                prop_attrs['subtype'] = 'FILE_NAME'
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

            m = re.fullmatch('color(\d)', mx_type)
            if m:
                prop_type = FloatVectorProperty
                prop_attrs['subtype'] = 'COLOR'
                prop_attrs['size'] = int(m[1])
                break

            m = re.fullmatch('vector(\d)', mx_type)
            if m:
                prop_type = FloatVectorProperty
                prop_attrs['subtype'] = 'XYZ'
                prop_attrs['size'] = int(m[1])
                break

            raise NotImplementedError("Unsupported mx_type", mx_type, prop_name)

        prop_attrs['name'] = mx_param.getAttribute('uiname') if mx_param.hasAttribute('uiname')\
            else prop_name.title()
        prop_attrs['description'] = mx_param.getAttribute('doc')

        if mx_param.hasAttribute('uimin'):
            prop_attrs['min'] = parse_val(prop_type, mx_param.getAttribute('uimin'))
        if mx_param.hasAttribute('uimax'):
            prop_attrs['max'] = parse_val(prop_type, mx_param.getAttribute('uimax'))
        if mx_param.hasAttribute('uisoftmin'):
            prop_attrs['soft_min'] = parse_val(prop_type, mx_param.getAttribute('uisoftmin'))
        if mx_param.hasAttribute('uisoftmax'):
            prop_attrs['soft_max'] = parse_val(prop_type, mx_param.getAttribute('uisoftmax'))

        if mx_param.hasAttribute('value'):
            prop_attrs['default'] = parse_val(prop_type, mx_param.getAttribute('value'))

        return prop_name, prop_type, prop_attrs

    def create_input(self, mx_input):
        pass

    def create_output(self, mx_output):
        pass


def parse_val(prop_type, val):
    if prop_type == StringProperty:
        return val
    if prop_type == IntProperty:
        return int(val)
    if prop_type == FloatProperty:
        return float(val)
    if prop_type == BoolProperty:
        return val == "true"
    if prop_type == FloatVectorProperty:
        return tuple(float(x) for x in val.split(','))
    if prop_type == EnumProperty:
        return tuple(x.strip() for x in val.split(','))


def parse_value(mx_type, val_str, only_first=False):
    val = None
    if mx_type == 'float':
        val = float(val_str)
    elif mx_type.startswith('color') or mx_type.startswith('vector') and 'array' not in mx_type:
        val = [float(x) for x in val_str.split(',')]
    elif mx_type == 'string':
        val = val_str
    elif mx_type == 'integer':
        val = int(val_str)
    elif mx_type == 'filename':
        val = val_str
    elif mx_type == 'boolean':
        val = val_str.lower() == 'true'

    if only_first and isinstance(val, list):
        val = val[0]

    return val


def get_param(mx_param):
    ''' convert a mx param into a blender property '''
    mx_param_type = mx_param.getType()
    name = mx_param.getName()
    prop_attrs = {
        'name': prettify_string(name)
    }

    # handle ui attrs:
    if mx_param.hasValueString():
        prop_attrs['default'] = parse_value(mx_param_type, mx_param.getValueString())
    if mx_param.hasAttribute('uimin'):
        prop_attrs['min'] = parse_value(mx_param_type, mx_param.getAttribute('uimin'),
                                        only_first=True)
    if mx_param.hasAttribute('uimax'):
        prop_attrs['max'] = parse_value(mx_param_type, mx_param.getAttribute('uimax'),
                                        only_first=True)
    if mx_param.hasAttribute('uisoftmin'):
        prop_attrs['soft_min'] = parse_value(mx_param_type, mx_param.getAttribute('uisoftmin'),
                                             only_first=True)
    if mx_param.hasAttribute('uisoftmax'):
        prop_attrs['soft_max'] = parse_value(mx_param_type, mx_param.getAttribute('uisoftmax'),
                                             only_first=True)

    if mx_param_type == 'float':
        return bpy.props.FloatProperty, prop_attrs

    elif mx_param_type.startswith('color'):
        prop_attrs['size'] = int(mx_param_type[-1])
        prop_attrs['subtype'] = 'COLOR'
        return bpy.props.FloatVectorProperty, prop_attrs

    elif mx_param_type == 'string':
        return bpy.props.StringProperty, prop_attrs

    elif mx_param_type == 'integer':
        return bpy.props.IntProperty, prop_attrs

    elif mx_param_type == 'filename':
        prop_attrs['subtype'] = 'FILE_NAME'
        return bpy.props.StringProperty, prop_attrs

    elif mx_param_type == 'boolean':
        return bpy.props.BoolProperty, prop_attrs

    elif mx_param_type.startswith('vector') and 'array' not in mx_param_type:
        prop_attrs['size'] = int(mx_param_type[-1])
        prop_attrs['subtype'] = 'XYZ'
        return bpy.props.FloatVectorProperty, prop_attrs

    else:
        raise ValueError('Unknown type', mx_param_type)


def create_node_types(file_paths):
    node_types = []
    for p in file_paths:
        doc = mx.createDocument()
        mx.readFromXmlFile(doc, str(p))
        mx_node_defs = doc.getNodeDefs()
        for mx_node_def in mx_node_defs:
            try:
                node_type = MxNode.create_node_type(mx_node_def)
                node_types.append(node_type)
            except Exception as e:
                log.error(e)

    return node_types
