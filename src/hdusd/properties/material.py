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

from . import HdUSDProperties
from ..mx_nodes.node_tree import MxNodeTree
from ..bl_nodes.nodes import ShaderNodeOutputMaterial


from ..utils import logging
log = logging.Log(tag='export.material')


class MaterialProperties(HdUSDProperties):
    bl_type = bpy.types.Material

    def update_mx_node_tree(self, context):
        self.reset()

    mx_node_tree: bpy.props.PointerProperty(type=MxNodeTree, update=update_mx_node_tree)

    @property
    def output_node(self):
        material = self.id_data
        return next((node for node in material.node_tree.nodes if
                     node.bl_idname == ShaderNodeOutputMaterial.__name__ and
                     node.is_active_output), None)

    def export(self, obj: bpy.types.Object) -> [mx.Document, None]:
        if self.mx_node_tree:
            return self.mx_node_tree.export()

        material = self.id_data
        output_node = self.output_node

        if not output_node:
            return None

        doc = mx.createDocument()

        node_parser = ShaderNodeOutputMaterial(doc, material, output_node, obj,
                                               rpr=bpy.context.scene.hdusd.use_rpr_mx_nodes)
        node_parser.export()

        return doc

    def reset(self):
        print("reset", self)


def depsgraph_update(depsgraph):
    if not depsgraph.updates:
        return

    update_id = depsgraph.updates[0].id
    if isinstance(update_id, bpy.types.Material):
        update_id.hdusd.reset()
