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
import MaterialX as mx

import bpy
from bpy_extras.io_utils import ExportHelper

from . import HdUSD_Panel, HdUSD_Operator
from ..mx_nodes.node_tree import MxNodeTree

from ..utils import logging
log = logging.Log(tag='ui.mx_nodes')


class HDUSD_MX_OP_import_file(HdUSD_Operator, ExportHelper):
    bl_idname = "hdusd.mx_import_file"
    bl_label = "Import Material"
    bl_description = "Import selected mtlx file"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    filename_ext = ".mtlx"
    filter_glob: bpy.props.StringProperty(default="*.mtlx", options={'HIDDEN'}, )

    # Perform the operator action.
    def execute(self, context):
        doc = mx.createDocument()
        try:
            mx.readFromXmlFile(doc, self.filepath)

        except mx.ExceptionFileMissing as err:
            log.error(err, self.filepath)
            return {'CANCELLED'}

        except mx.ExceptionParseError as err:
            log.error("Invalid MaterialX XML file", self.filepath, err)
            return {'CANCELLED'}

        # # create sub node graphs
        # for sub_ng in doc.getNodeGraphs():
        #     create_node_graph(doc, sub_ng)

        # for mat in materials:
        #     # material in materialx takes the first node as the shader
        #     print("creating mat", mat.getName())
        #
        #     # create material nodetree
        #     nt = bpy.data.node_groups.new(mat.getName(), 'mx.NodeTree')
        #     mat_node = nt.nodes.new("mx.surfacematerial")
        #
        #     # surface
        #     for i, s_ref in enumerate(mat.getShaderRefs()):
        #         created_item = create_item_from_shaderref(doc, s_ref, nt)
        #         if created_item:
        #             # TODO should be smarter about hooking up types
        #             nt.links.new(mat_node.inputs[i], created_item.outputs[0])

        return {"FINISHED"}


class HDUSD_MX_OP_export_file(HdUSD_Operator, ExportHelper):
    bl_idname = "hdusd.mx_export_file"
    bl_label = "Export to File"
    bl_description = "Export MaterialX node tree to .mtlx file"

    filename_ext = ".mtlx"
    filepath: bpy.props.StringProperty(
        name="File Path",
        description="File path used for exporting MaterialX node tree to .mtlx file",
        maxlen=1024, subtype="FILE_PATH"
    )
    filter_glob: bpy.props.StringProperty(default="*.mtlx", options={'HIDDEN'}, )

    def execute(self, context):
        mx_node_tree = context.space_data.edit_tree
        doc = mx_node_tree.export()
        if not doc:
            log.warn("Incorrect node tree to export", mx_node_tree)
            return {'CANCELLED'}

        mx.writeToXmlFile(doc, self.filepath)
        return {'FINISHED'}

    @staticmethod
    def enabled(context):
        return bool(context.space_data.edit_tree.output_node)


class HDUSD_MX_OP_export_console(HdUSD_Operator):
    bl_idname = "hdusd.mx_export_console"
    bl_label = "Export to Console"
    bl_description = "Export MaterialX node tree to console"

    def execute(self, context):
        mx_node_tree = context.space_data.edit_tree
        doc = mx_node_tree.export()
        if not doc:
            log.warn("Incorrect node tree to export", mx_node_tree)
            return {'CANCELLED'}

        print(mx.writeToXmlString(doc))
        return {'FINISHED'}

    @staticmethod
    def enabled(context):
        return bool(context.space_data.edit_tree.output_node)


class HDUSD_MX_OP_create_basic_nodes(HdUSD_Operator):
    bl_idname = "hdusd.mx_create_basic_nodes"
    bl_label = "Create Basic Nodes"
    bl_description = "Create basic MaterialX nodes"

    def execute(self, context):
        mx_node_tree = context.space_data.edit_tree
        mx_node_tree.create_basic_nodes()
        return {"FINISHED"}


class HDUSD_MX_MATERIAL_PT_import_export(HdUSD_Panel):
    bl_label = "Import/Export"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Tool"

    @classmethod
    def poll(cls, context):
        tree = context.space_data.edit_tree
        return super().poll(context) and tree and tree.bl_idname == MxNodeTree.bl_idname

    def draw(self, context):
        layout = self.layout

        layout.operator(HDUSD_MX_OP_create_basic_nodes.bl_idname)

        col = layout.column()
        col.enabled = HDUSD_MX_OP_export_file.enabled(context)
        col.operator(HDUSD_MX_OP_export_file.bl_idname)
        col.operator(HDUSD_MX_OP_export_console.bl_idname)
