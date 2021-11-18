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
import shutil
import bpy
import os

from bpy_extras.io_utils import ImportHelper, ExportHelper
from pathlib import Path

from . import HdUSD_Panel, HdUSD_Operator
from ..mx_nodes.node_tree import MxNodeTree
from ..utils import mx as mx_utils

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
    bl_label = "Export to File"
    bl_description = "Export MaterialX node tree to .mtlx file"

    filename_ext = ".mtlx"
    filepath: bpy.props.StringProperty(
        name="File Path",
        description="File path used for exporting MaterialX node tree to .mtlx file",
        maxlen=1024, subtype="FILE_PATH"
    )
    filter_glob: bpy.props.StringProperty(default="*.mtlx", options={'HIDDEN'}, )

    is_export_deps: bpy.props.BoolProperty(name="Export MaterialX dependencies",
                                           description="Export used MaterialX dependencies",
                                           default=False)

    is_export_textures: bpy.props.BoolProperty(name="Export bound textures",
                                               description="Export bound textures to corresponded folder",
                                               default=True)

    texture_dir_name: bpy.props.StringProperty(
        name="Texture folder name",
        description="Texture folder name used for exporting files",
        default='Textures',
        maxlen=1024
    )

    def execute(self, context):
        mx_node_tree = context.space_data.edit_tree
        doc = mx_node_tree.export()
        if not doc:
            log.warn("Incorrect node tree to export", mx_node_tree)
            return {'CANCELLED'}

        root_dir = Path(self.filepath).parent

        if self.is_export_deps:
            mx_libs_dir = root_dir / mx_utils.MX_LIBS_FOLDER
            if os.path.isdir(mx_libs_dir):
                shutil.rmtree(mx_libs_dir)

            for mtlx_path in set(node._file_path for node in mx_node_tree.nodes):
                source_path = mx_utils.MX_LIBS_DIR.parent / mtlx_path
                dest_path = root_dir / mtlx_path
                rel_dest_path = os.path.relpath(dest_path, root_dir / mx_utils.MX_LIBS_FOLDER)
                dest_path = root_dir / rel_dest_path
                Path(dest_path.parent).mkdir(parents=True, exist_ok=True)
                shutil.copy(source_path, dest_path)
                mx.prependXInclude(doc, rel_dest_path)

        if self.is_export_textures:
            texture_dir = root_dir / self.texture_dir_name
            if os.path.isdir(texture_dir):
                shutil.rmtree(texture_dir)

            Path(texture_dir).mkdir(parents=True, exist_ok=True)
            image_paths = set()

            i = 0

            input_files = tuple(v for v in doc.traverseTree() if isinstance(v, mx.Input) and v.getType() == 'filename')
            for mx_input in input_files:
                source_path = mx_input.getValue()
                dest_path = texture_dir / Path(source_path).name

                if source_path not in image_paths:
                    image_paths.update([source_path])

                    if os.path.isfile(dest_path):
                        i += 1
                        dest_path = texture_dir / f"{Path(source_path).stem}_{i}{Path(source_path).suffix}"
                    else:
                        dest_path = texture_dir / f"{Path(source_path).stem}{Path(source_path).suffix}"

                    shutil.copy(source_path, dest_path)
                    log(f"Export file {source_path} to {dest_path}: completed successfuly")

                rel_dest_path = os.path.relpath(dest_path, root_dir)
                mx_input.setValue(rel_dest_path, mx_input.getType())

        mx.writeToXmlFile(doc, self.filepath)
        log(f"Export MaterialX to {self.filepath}: completed successfuly")

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
        layout.operator(HDUSD_MX_OP_import_file.bl_idname)

        col = layout.column()
        col.enabled = HDUSD_MX_OP_export_file.enabled(context)
        col.operator(HDUSD_MX_OP_export_file.bl_idname)
        col.operator(HDUSD_MX_OP_export_console.bl_idname)
