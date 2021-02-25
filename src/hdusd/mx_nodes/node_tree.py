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
from collections import defaultdict

import MaterialX as mx

import bpy

from .nodes import get_mx_node_cls
from ..utils import mx as mx_utils


NODE_SEPARATION_WIDTH = 70


class MxNodeTree(bpy.types.ShaderNodeTree):
    """
    MaterialX NodeTree
    """
    bl_label = "MaterialX"
    bl_icon = "NODE_MATERIAL"
    bl_idname = "hdusd.MxNodeTree"
    COMPAT_ENGINES = {'HdUSD'}

    @classmethod
    def poll(cls, context):
        return context.engine in cls.COMPAT_ENGINES

    @property
    def output_node(self):
        return next((node for node in self.nodes
                     if node.bl_idname == 'hdusd.MxNode_STD_surfacematerial'), None)

    @property
    def output_node_volume(self):
        return next((node for node in self.nodes
                     if node.bl_idname == 'hdusd.MxNode_STD_volumematerial'), None)

    def export(self) -> mx.Document:
        output_node = self.output_node
        if not output_node:
            return None

        doc = mx.createDocument()
        doc.setVersionString("1.38")

        surfacematerial = output_node.compute(0, doc=doc)
        if not surfacematerial:
            return None

        return doc

    def import_(self, doc: mx.Document):
        self.nodes.clear()
        layers = {}

        def import_node(mx_node, layer):
            name = mx_node.getName()
            if name in self.nodes:
                layers[name] = max(layers[name], layer)
                return self.nodes[name]

            MxNode_cls = get_mx_node_cls(mx_node.getCategory(), mx_node.getType())
            node = self.nodes.new(MxNode_cls.bl_idname)
            node.name = name
            layers[name] = layer

            node.data_type = mx_node.getType()
            for mx_param in mx_node.getParameters():
                node.set_param_value(mx_param.getName(),
                                     mx_utils.parse_value(mx_param.getValue(), mx_param.getType()))

            for mx_input in mx_node.getInputs():
                input_name = mx_input.getName()
                val = mx_input.getValue()
                if val is not None:
                    node.set_input_default(input_name,
                                           mx_utils.parse_value(val, mx_input.getType()))
                    continue

                node_name = mx_input.getNodeName()
                if node_name:
                    new_mx_node = doc.getNode(node_name)
                    new_node = import_node(new_mx_node, layer + 1)
                    self.links.new(new_node.outputs[0], node.inputs[input_name])

            return node

        mx_node = next(n for n in doc.getNodes() if n.getCategory() == 'surfacematerial')
        import_node(mx_node, 0)

        # placing nodes by layers
        node_layers = [[] for _ in range(max(layers.values()) + 1)]
        for node in self.nodes:
            node_layers[layers[node.name]].append(node.name)

        loc_x = 0
        for i, node_names in enumerate(node_layers):
            width = max(self.nodes[name].bl_width_default for name in node_names)
            loc_x -= (width + NODE_SEPARATION_WIDTH) if i > 0 else 0
            loc_y = 0
            for name in node_names:
                node = self.nodes[name]
                node.location = (loc_x, loc_y)
                loc_y -= node.height + NODE_SEPARATION_WIDTH

    def create_basic_nodes(self, node_name='PBR_standard_surface'):
        """ Reset basic node tree structure using scene or USD file as an input """
        self.nodes.clear()

        mat_node = self.nodes.new('hdusd.MxNode_STD_surfacematerial')
        if node_name == 'PBR_standard_surface':
            node = self.nodes.new(f'hdusd.MxNode_{node_name}')
            node.location = (mat_node.location[0] - node.bl_width_default - NODE_SEPARATION_WIDTH,
                             mat_node.location[1])
            self.links.new(node.outputs[0], mat_node.inputs[0])
        else:
            surface_node = self.nodes.new('hdusd.MxNode_PBR_surface')
            surface_node.location = (mat_node.location[0] - surface_node.width -
                                     NODE_SEPARATION_WIDTH, mat_node.location[1])
            self.links.new(surface_node.outputs[0], mat_node.inputs[0])

            node = self.nodes.new(f'hdusd.MxNode_{node_name}')
            node.location = (surface_node.location[0] - node.width - NODE_SEPARATION_WIDTH,
                             surface_node.location[1])
            self.links.new(node.outputs[0], surface_node.inputs[0])
