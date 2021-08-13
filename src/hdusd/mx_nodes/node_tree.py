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

import ntpath


NODE_LAYER_SEPARATION_WIDTH = 280
NODE_LAYER_SHIFT_X = 30
NODE_LAYER_SHIFT_Y = 100


class MxNodeTree(bpy.types.ShaderNodeTree):
    """
    MaterialX NodeTree
    """
    bl_label = "MaterialX"
    bl_icon = "NODE_MATERIAL"
    bl_idname = "hdusd.MxNodeTree"
    COMPAT_ENGINES = {'HdUSD'}

    _do_update = True

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

    def no_update_call(self, op, *args, **kwargs):
        """This function prevents call of self.update() during calling our function"""
        if not self._do_update:
            return op(*args, **kwargs)

        self._do_update = False
        try:
            return op(*args, **kwargs)
        finally:
            self._do_update = True

    def export(self) -> mx.Document:
        output_node = self.output_node
        if not output_node:
            return None

        doc = mx.createDocument()

        surfacematerial = output_node.compute(0, doc=doc)
        if not surfacematerial:
            return None

        return doc

    def import_(self, doc: mx.Document, file_path):
        def do_import():
            self.nodes.clear()
            layers = {}

            def import_node(mx_node, layer):
                mx_nodegraph = mx_node.getParent()
                node_path = mx_node.getNamePath()
                file_prefix = mx_utils.get_file_prefix(mx_node, file_path)

                if node_path in self.nodes:
                    layers[node_path] = max(layers[node_path], layer)
                    return self.nodes[node_path]

                MxNode_cls = get_mx_node_cls(mx_node.getCategory(), mx_node.getType())
                node = self.nodes.new(MxNode_cls.bl_idname)
                node.name = node_path
                layers[node_path] = layer

                node.data_type = mx_node.getType()
                for mx_param in mx_node.getParameters():
                    node.set_param_value(
                        mx_param.getName(),
                        mx_utils.parse_value(mx_param.getValue(), mx_param.getType(), file_prefix))

                for mx_input in mx_node.getInputs():
                    input_name = mx_input.getName()
                    val = mx_input.getValue()
                    if val is not None:
                        node.set_input_default(
                            input_name,
                            mx_utils.parse_value(val, mx_input.getType(), file_prefix))
                        continue

                    node_name = mx_input.getNodeName()
                    if node_name:
                        new_mx_node = mx_nodegraph.getNode(node_name)
                        new_node = import_node(new_mx_node, layer + 1)
                        self.links.new(new_node.outputs[0], node.inputs[input_name])
                        continue

                    new_nodegraph_name = mx_input.getAttribute('nodegraph')
                    if new_nodegraph_name:
                        output_name = mx_input.getAttribute('output')
                        new_mx_nodegraph = mx_nodegraph.getNodeGraph(new_nodegraph_name)
                        mx_output = new_mx_nodegraph.getOutput(output_name)
                        node_name = mx_output.getNodeName()
                        new_mx_node = new_mx_nodegraph.getNode(node_name)
                        new_node = import_node(new_mx_node, layer + 1)
                        self.links.new(new_node.outputs[0], node.inputs[input_name])
                        continue

                node.ui_folders_check()
                return node

            mx_node = next(n for n in doc.getNodes() if n.getCategory() == 'surfacematerial')
            import_node(mx_node, 0)

            # placing nodes by layers
            node_layers = [[] for _ in range(max(layers.values()) + 1)]
            for node in self.nodes:
                node_layers[layers[node.name]].append(node.name)

            loc_x = 0
            for i, node_names in enumerate(node_layers):
                loc_y = 0
                for name in node_names:
                    node = self.nodes[name]
                    node.location = (loc_x, loc_y)
                    loc_y -= NODE_LAYER_SHIFT_Y
                    loc_x -= NODE_LAYER_SHIFT_X

                loc_x -= NODE_LAYER_SEPARATION_WIDTH

        self.no_update_call(do_import)
        self.update_()

    def create_basic_nodes(self, node_name='PBR_standard_surface'):
        """ Reset basic node tree structure using scene or USD file as an input """
        def create_nodes():
            self.nodes.clear()

            mat_node = self.nodes.new('hdusd.MxNode_STD_surfacematerial')
            node = self.nodes.new(f'hdusd.MxNode_{node_name}')
            node.location = (mat_node.location[0] - NODE_LAYER_SEPARATION_WIDTH,
                             mat_node.location[1])
            self.links.new(node.outputs[0], mat_node.inputs[0])

        self.no_update_call(create_nodes)
        self.update_()

    # this is called from Blender
    def update(self):
        if not self._do_update:
            return

        self.update_()

    def update_(self):
        for material in bpy.data.materials:
            if material.hdusd.mx_node_tree and material.hdusd.mx_node_tree.name == self.name:
                material.hdusd.update()

        ng = bpy.data.node_groups.get(self.name, None)
        if ng is None:
            return

        nodes = ng.nodes
        if nodes is None:
            return

        for node in nodes:
            if not hasattr(node.prop, 'p_file'):
                continue

            file = node.prop.p_file
            if not file:
                continue

            filepath = file.filepath
            if not filepath:
                continue

            if bpy.data.images.get(ntpath.basename(bpy.path.abspath(filepath)), None) is not None:
                continue

            bpy.ops.image.open(filepath=file)