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
import traceback

from . import HdUSDProperties
from ..mx_nodes.node_tree import MxNodeTree
from ..bl_nodes.nodes import ShaderNodeOutputMaterial
from ..usd_nodes import node_tree as usd_node_tree
from ..engine.viewport_engine import ViewportEngineScene
from ..utils.mx import MX_LIBS_DIR

from ..utils import logging, get_temp_file
log = logging.Log('properties.material')


class MaterialProperties(HdUSDProperties):
    bl_type = bpy.types.Material

    def update_mx_node_tree(self, context):
        self.update()

    mx_node_tree: bpy.props.PointerProperty(type=MxNodeTree, update=update_mx_node_tree)

    @property
    def output_node(self):
        material = self.id_data

        if not material.node_tree:
            return None

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

        node_parser = ShaderNodeOutputMaterial(doc, material, output_node, obj)
        if not node_parser.export():
            return None

        return doc

    def update(self, is_depsgraph=False):
        """
        Main update callback function, which notifies that material was updated from both:
        depsgraph or MaterialX node tree
        """
        if is_depsgraph and self.mx_node_tree:
            return

        material = self.id_data
        usd_node_tree.material_update(material)
        ViewportEngineScene.material_update(material)

    def convert_shader_to_mx(self, obj: bpy.types.Object = None):
        mat = self.id_data
        output_node = self.output_node
        if not output_node:
            log.warn("Incorrect node tree to export: output node doesn't exist")
            return False

        mx_node_tree = bpy.data.node_groups.new(f"MX_{mat.name}", type=MxNodeTree.bl_idname)

        if obj:
            doc = self.export(obj)
        else:
            doc = mx.createDocument()

            node_parser = ShaderNodeOutputMaterial(doc, mat, output_node, obj)
            if not node_parser.export():
                return False

        if not doc:
            log.warn("Incorrect node tree to export", mx_node_tree)
            return False

        mtlx_file = get_temp_file(".mtlx",
                                  f'{mat.name}_{self.mx_node_tree.name if self.mx_node_tree else ""}')
        mx.writeToXmlFile(doc, str(mtlx_file))
        search_path = mx.FileSearchPath(str(mtlx_file.parent))
        search_path.append(str(MX_LIBS_DIR))

        try:
            mx.readFromXmlFile(doc, str(mtlx_file), searchPath=search_path)
            mx_node_tree.import_(doc, mtlx_file)
            self.mx_node_tree = mx_node_tree
        except Exception as e:
            log.error(traceback.format_exc(), mtlx_file)
            return False

        return True


def depsgraph_update(depsgraph):
    if not depsgraph.updates:
        return

    # Undo operation sends modified object with other stuff (scene, collection, etc...)
    mat = next((upd.id for upd in depsgraph.updates if isinstance(upd.id, bpy.types.Material)), None)
    if mat:
        mat.hdusd.update(True)
