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
from . import log


NODE_LAYER_SEPARATION_WIDTH = 280
NODE_LAYER_SHIFT_X = 30
NODE_LAYER_SHIFT_Y = 100
AREA_TO_UPDATE = 'PROPERTIES'
REGION_TO_UPDATE = 'WINDOW'


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
        def prepare_for_import():
            surfacematerial = next(
                (n for n in doc.getNodes() if n.getCategory() == 'surfacematerial'), None)
            if surfacematerial:
                return

            mat = doc.getMaterials()[0]
            sr = mat.getShaderRefs()[0]

            doc.removeMaterial(mat.getName())

            node_name = sr.getName()
            if not node_name.startswith("SR_"):
                node_name = f"SR_{node_name}"
            node = doc.addNode(sr.getNodeString(), node_name, 'surfaceshader')
            for sr_input in sr.getBindInputs():
                input = node.addInput(sr_input.getName(), sr_input.getType())
                ng_name = sr_input.getNodeGraphString()
                if ng_name:
                    input.setAttribute('nodegraph', ng_name)
                    input.setAttribute('output', sr_input.getOutputString())
                else:
                    input.setValue(sr_input.getValue())

            surfacematerial = doc.addNode('surfacematerial', mat.getName(), 'material')
            input = surfacematerial.addInput('surfaceshader', node.getType())
            input.setNodeName(node.getName())

        def do_import():
            self.nodes.clear()

            def import_node(mx_node, mx_output_name=None, look_nodedef=True):
                mx_nodegraph = mx_node.getParent()
                node_path = mx_node.getNamePath()
                file_prefix = mx_utils.get_file_prefix(mx_node, file_path)

                if node_path in self.nodes:
                    return self.nodes[node_path]

                try:
                    MxNode_cls, data_type = get_mx_node_cls(mx_node)

                except KeyError as e:
                    if not look_nodedef:
                        log.warn(e)
                        return None

                    # looking for nodedef and switching to another nodegraph defined in doc
                    nodedef = next(nd for nd in doc.getNodeDefs()
                                   if nd.getNodeString() == mx_node.getCategory() and
                                   nd.getType() == mx_node.getType())
                    new_mx_nodegraph = next(ng for ng in doc.getNodeGraphs()
                                            if ng.getNodeDefString() == nodedef.getName())

                    mx_output = new_mx_nodegraph.getActiveOutput(mx_output_name)
                    node_name = mx_output.getNodeName()
                    new_mx_node = new_mx_nodegraph.getNode(node_name)

                    return import_node(new_mx_node, None, False)

                node = self.nodes.new(MxNode_cls.bl_idname)
                node.name = node_path
                node.data_type = data_type
                nodedef = node.nodedef

                for mx_input in mx_node.getActiveInputs():
                    input_name = mx_input.getName()
                    nd_input = nodedef.getActiveInput(input_name)
                    if nd_input.getAttribute('uniform') == 'true':
                        node.set_param_value(input_name,mx_utils.parse_value(
                            node, mx_input.getValue(), mx_input.getType(), file_prefix))
                        continue

                    if input_name not in node.inputs:
                        log.error(f"Incorrect input name '{input_name}' for node {node}")
                        continue

                    val = mx_input.getValue()
                    if val is not None:
                        node.set_input_value(
                            input_name,
                            mx_utils.parse_value(node, val, mx_input.getType(), file_prefix))
                        continue

                    node_name = mx_input.getNodeName()

                    if node_name:
                        new_mx_node = mx_nodegraph.getNode(node_name)
                        if not new_mx_node:
                            log.error(f"Couldn't find node '{node_name}' in nodegraph '{mx_nodegraph.getNamePath()}'")
                            continue

                        new_node = import_node(new_mx_node)

                        out_name = mx_input.getAttribute('output')
                        if len(new_node.nodedef.getActiveOutputs()) > 1 and out_name:
                            new_node_output = new_node.outputs[out_name]
                        else:
                            new_node_output = new_node.outputs[0]

                        self.links.new(new_node_output, node.inputs[input_name])
                        continue

                    new_nodegraph_name = mx_input.getAttribute('nodegraph')
                    if new_nodegraph_name:
                        mx_output_name = mx_input.getAttribute('output')
                        new_mx_nodegraph = mx_nodegraph.getNodeGraph(new_nodegraph_name)
                        mx_output = new_mx_nodegraph.getActiveOutput(mx_output_name)
                        node_name = mx_output.getNodeName()
                        new_mx_node = new_mx_nodegraph.getNode(node_name)
                        new_node = import_node(new_mx_node, mx_output_name)
                        if not new_node:
                            continue

                        out_name = mx_output.getAttribute('output')
                        if len(new_node.nodedef.getActiveOutputs()) > 1 and out_name:
                            new_node_output = new_node.outputs[out_name]
                        else:
                            new_node_output = new_node.outputs[0]

                        self.links.new(new_node_output, node.inputs[input_name])
                        continue

                node.check_ui_folders()
                return node

            mx_node = next(n for n in doc.getNodes() if n.getCategory() == 'surfacematerial')
            output_node = import_node(mx_node, 0)

            if not output_node:
                return

            # arranging nodes by layers
            layer = {output_node}
            layer_index = 0
            layers = {}
            while layer:
                new_layer = set()
                for node in layer:
                    layers[node] = layer_index
                    for inp in node.inputs:
                        for link in inp.links:
                            new_layer.add(link.from_node)
                layer = new_layer
                layer_index += 1

            node_layers = [[] for _ in range(max(layers.values()) + 1)]
            for node in self.nodes:
                node_layers[layers[node]].append(node)

            # placing nodes by layers
            loc_x = 0
            for i, nodes in enumerate(node_layers):
                loc_y = 0
                for node in nodes:
                    node.location = (loc_x, loc_y)
                    loc_y -= NODE_LAYER_SHIFT_Y
                    loc_x -= NODE_LAYER_SHIFT_X

                loc_x -= NODE_LAYER_SEPARATION_WIDTH

        prepare_for_import()
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
        self.update_links()

        for material in bpy.data.materials:
            if material.hdusd.mx_node_tree and material.hdusd.mx_node_tree.name == self.name:
                material.hdusd.update()

        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == AREA_TO_UPDATE:
                    for region in area.regions:
                        if region.type == REGION_TO_UPDATE:
                            region.tag_redraw()

    def update_links(self):
        for link in self.links:
            socket_from_type = link.from_socket.node.nodedef.getActiveOutput(link.from_socket.name).getType()
            socket_to_type = link.to_socket.node.nodedef.getActiveInput(link.to_socket.name).getType()

            if socket_to_type != socket_from_type:
                link.is_valid = False
                continue

            link.is_valid = True
