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
import bpy

import MaterialX as mx


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
                     if node.bl_idname == 'hdusd.MxNode_surfacematerial'), None)

    @property
    def output_node_volume(self):
        return next((node for node in self.nodes
                     if node.bl_idname == 'hdusd.MxNode_volumematerial'), None)

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

    def create_basic_nodes(self, node_name='standard_surface'):
        """ Reset basic node tree structure using scene or USD file as an input """
        self.nodes.clear()
        SEP_WIDTH = 70

        mat_node = self.nodes.new('hdusd.MxNode_surfacematerial')
        if node_name == 'standard_surface':
            node = self.nodes.new('hdusd.MxNode_standard_surface')
            node.location = (mat_node.location[0] - node.width - SEP_WIDTH,
                             mat_node.location[1])
            self.links.new(node.outputs[0], mat_node.inputs[0])
        else:
            surface_node = self.nodes.new('hdusd.MxNode_surface')
            surface_node.location = (mat_node.location[0] - surface_node.width - SEP_WIDTH,
                                     mat_node.location[1])
            self.links.new(surface_node.outputs[0], mat_node.inputs[0])

            node = self.nodes.new('hdusd.MxNode_' + node_name)
            node.location = (surface_node.location[0] - node.width - SEP_WIDTH,
                             surface_node.location[1])
            self.links.new(node.outputs[0], surface_node.inputs[0])
