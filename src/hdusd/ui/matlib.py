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
import traceback

import MaterialX as mx

import bpy

from . import HdUSD_Panel, HdUSD_Operator
from ..mx_nodes.node_tree import MxNodeTree
from ..utils import mx as mx_utils

from ..utils import logging
log = logging.Log(tag='ui.matlib')


class HDUSD_MATLIB_OP_import_material(HdUSD_Operator):
    """Import Material"""
    bl_idname = "hdusd.matlib_import_material"
    bl_label = "Import Material"

    def execute(self, context):
        matlib_prop = context.window_manager.hdusd.matlib
        material = matlib_prop.pcoll.materials[matlib_prop.material]

        # unzipping package
        package = material.packages[0]
        package.get_info()
        package.get_file()
        mtlx_file = package.unzip()

        # getting/creating MxNodeTree
        bl_material = context.material
        mx_node_tree = bl_material.hdusd.mx_node_tree
        if not bl_material.hdusd.mx_node_tree:
            mx_node_tree = bpy.data.node_groups.new(f"MX_{bl_material.name}",
                                                    type=MxNodeTree.bl_idname)
            bl_material.hdusd.mx_node_tree = mx_node_tree

        log("Reading", mtlx_file)
        doc = mx.createDocument()
        search_path = mx.FileSearchPath(str(mtlx_file.parent))
        search_path.append(str(mx_utils.MX_LIBS_DIR))
        try:
            mx.readFromXmlFile(doc, str(mtlx_file), searchPath=search_path)
            mx_node_tree.import_(doc, mtlx_file)

        except Exception as e:
            log.error(traceback.format_exc(), mtlx_file)
            return {'CANCELLED'}

        return {"FINISHED"}


class HDUSD_MATLIB_PT_matlib(HdUSD_Panel):
    bl_label = "Material Library"
    bl_context = "material"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        matlib_prop = context.window_manager.hdusd.matlib

        layout.prop(matlib_prop, "category")
        layout.template_icon_view(matlib_prop, "material")

        row = layout.row()
        row.enabled = bool(context.material)
        row.operator(HDUSD_MATLIB_OP_import_material.bl_idname)

