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

from bpy_extras.io_utils import ImportHelper, ExportHelper
from pathlib import Path

from . import HdUSD_Panel, HdUSD_ChildPanel, HdUSD_Operator
from ..mx_nodes.node_tree import MxNodeTree
from ..utils import mx as mx_utils
from .. import config

from ..utils import logging
log = logging.Log('ui.mx_nodes')


class HDUSD_MX_OP_import_file(HdUSD_Operator, ImportHelper):
    bl_idname = "hdusd.mx_import_file"
    bl_label = "Import from File"
    bl_description = "Import MaterialX node tree from .mtlx file"

    filename_ext = ".mtlx"
    filepath: bpy.props.StringProperty(
        name="File Path",
        description="File path used for importing MaterialX node tree from .mtlx file",
        maxlen=1024, subtype="FILE_PATH"
    )
    filter_glob: bpy.props.StringProperty(default="*.mtlx", options={'HIDDEN'}, )

    def execute(self, context):
        mx_node_tree = context.space_data.edit_tree
        mtlx_file = Path(self.filepath)

        doc = mx.createDocument()
        search_path = mx.FileSearchPath(str(mtlx_file.parent))
        search_path.append(str(mx_utils.MX_LIBS_DIR))
        try:
            mx.readFromXmlFile(doc, str(mtlx_file))
            mx_node_tree.import_(doc, mtlx_file)

        except Exception as e:
            log.error(traceback.format_exc(), mtlx_file)
            return {'CANCELLED'}

        return {'FINISHED'}


class HDUSD_MX_OP_export_file(HdUSD_Operator, ExportHelper):
    bl_idname = "hdusd.mx_export_file"
    bl_label = "Export MaterialX"
    bl_description = "Export MaterialX node tree to .mtlx file"

    # region properties
    filename_ext = ".mtlx"

    filepath: bpy.props.StringProperty(
        name="File Path",
        description="File path used for exporting MaterialX node tree to .mtlx file",
        maxlen=1024,
        subtype="FILE_PATH"
    )
    filter_glob: bpy.props.StringProperty(
        default="*.mtlx",
        options={'HIDDEN'},
    )
    is_export_deps: bpy.props.BoolProperty(
        name="Include dependencies",
        description="Export used MaterialX dependencies",
        default=False
    )
    is_export_textures: bpy.props.BoolProperty(
        name="Export bound textures",
        description="Export bound textures to corresponded folder",
        default=False
    )
    is_clean_texture_folder: bpy.props.BoolProperty(
        name="Сlean texture folder",
        description="Сlean texture folder before export",
        default=False
    )
    is_clean_deps_folders: bpy.props.BoolProperty(
        name="Сlean MaterialX dependencies folders",
        description="Сlean MaterialX dependencies folders before export",
        default=False
    )
    texture_dir_name: bpy.props.StringProperty(
        name="Texture folder name",
        description="Texture folder name used for exporting files",
        default='textures',
        maxlen=1024
    )
    # endregion

    def execute(self, context):
        mx_node_tree = context.space_data.edit_tree
        doc = mx_node_tree.export()
        if not doc:
            log.warn("Incorrect node tree to export", mx_node_tree)
            return {'CANCELLED'}

        mx_utils.export_mx_to_file(doc, self.filepath,
                                   mx_node_tree=mx_node_tree,
                                   is_export_deps=self.is_export_deps,
                                   is_export_textures=self.is_export_textures,
                                   texture_dir_name=self.texture_dir_name,
                                   is_clean_texture_folder=self.is_clean_texture_folder,
                                   is_clean_deps_folders=self.is_clean_deps_folders)

        return {'FINISHED'}

    def draw(self, context):
        self.layout.prop(self, 'is_export_deps')

        col = self.layout.column(align=False)
        col.prop(self, 'is_export_textures')

        row = col.row()
        row.enabled = self.is_export_textures
        row.prop(self, 'texture_dir_name', text='')

    @staticmethod
    def enabled(context):
        return bool(context.space_data.edit_tree.output_node)


class HDUSD_MX_OP_export_console(HdUSD_Operator):
    bl_idname = "hdusd.mx_export_console"
    bl_label = "Export MaterialX to Console"
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


class HDUSD_MX_MATERIAL_PT_tools(HdUSD_Panel):
    bl_label = "MaterialX Tools"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Tool"

    @classmethod
    def poll(cls, context):
        tree = context.space_data.edit_tree
        return super().poll(context) and tree and tree.bl_idname == MxNodeTree.bl_idname

    def draw(self, context):
        layout = self.layout

        layout.operator(HDUSD_MX_OP_create_basic_nodes.bl_idname, icon='ADD')
        layout.operator(HDUSD_MX_OP_import_file.bl_idname, icon='IMPORT')
        layout.operator(HDUSD_MX_OP_export_file.bl_idname, icon='EXPORT', text='Export MaterialX to file')


class HDUSD_MX_MATERIAL_PT_dev(HdUSD_ChildPanel):
    bl_label = "Dev"
    bl_parent_id = 'HDUSD_MX_MATERIAL_PT_tools'
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"

    @classmethod
    def poll(cls, context):
        return config.show_dev_settings

    def draw(self, context):
        layout = self.layout

        layout.operator(HDUSD_MX_OP_export_console.bl_idname)
