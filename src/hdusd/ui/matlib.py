# **********************************************************************
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
import textwrap

import MaterialX as mx

import bpy

from . import HdUSD_Panel, HdUSD_Operator
from ..mx_nodes.node_tree import MxNodeTree
from ..utils import mx as mx_utils
from ..utils.matlib import manager
from .. import config

from ..utils import logging
log = logging.Log('ui.matlib')


class HDUSD_MATERIAL_OP_matlib_clear_search(bpy.types.Operator):
    """Create new MaterialX node tree for selected material"""
    bl_idname = "hdusd.matlib_clear_search"
    bl_label = ""

    def execute(self, context):
        context.window_manager.hdusd.matlib.search = ''
        return {"FINISHED"}


class HDUSD_MATLIB_OP_load_materials(bpy.types.Operator):
    """Load materials"""
    bl_idname = "hdusd.matlib_load"
    bl_label = "Reload Library"

    def execute(self, context):
        manager.check_load_materials(reset=True)
        return {"FINISHED"}


class HDUSD_MATLIB_OP_import_material(HdUSD_Operator):
    """Import Material Package to material"""
    bl_idname = "hdusd.matlib_import_material"
    bl_label = "Import Material Package"

    def execute(self, context):
        matlib_prop = context.window_manager.hdusd.matlib
        package = matlib_prop.package

        mtlx_file = package.unzip()

        # getting/creating MxNodeTree
        bl_material = context.material
        mx_node_tree = bl_material.hdusd.mx_node_tree
        if not bl_material.hdusd.mx_node_tree:
            mx_node_tree = bpy.data.node_groups.new(f"MX_{bl_material.name}",
                                                    type=MxNodeTree.bl_idname)
            bl_material.hdusd.mx_node_tree = mx_node_tree

        log(f"Reading: {mtlx_file}")
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


class HDUSD_MATLIB_OP_load_package(HdUSD_Operator):
    """Download material package"""
    bl_idname = "hdusd.matlib_load_package"
    bl_label = "Download Package"

    def execute(self, context):
        matlib_prop = context.window_manager.hdusd.matlib
        manager.load_package(matlib_prop.package)

        return {"FINISHED"}


class HDUSD_MATLIB_PT_matlib(HdUSD_Panel):
    bl_idname = "HDUSD_MATLIB_PT_matlib"
    bl_label = "Material Library"
    bl_context = "material"
    bl_region_type = 'WINDOW'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return super().poll(context) and config.matlib_enabled

    def draw(self, context):
        layout = self.layout
        matlib_prop = context.window_manager.hdusd.matlib

        manager.check_load_materials()

        # category
        layout.prop(matlib_prop, 'category_id')

        # search
        row = layout.row(align=True)
        row.prop(matlib_prop, 'search', text="", icon='VIEWZOOM')
        if matlib_prop.search:
            row.operator(HDUSD_MATERIAL_OP_matlib_clear_search.bl_idname, icon='X')

        # materials
        col = layout.column(align=True)
        materials = matlib_prop.get_materials()
        if not materials:
            col.label(text="Start syncing..." if not manager.materials else "No materials found")
            return

        row = col.row()
        row.alignment = 'RIGHT'
        row.label(text=f"{len(materials)} materials")

        col.template_icon_view(matlib_prop, 'material_id', show_labels=True)

        mat = matlib_prop.material
        if not mat:
            return

        # other material renders
        if len(mat.renders) > 1:
            grid = col.grid_flow(align=True)
            for i, render in enumerate(mat.renders):
                if i % 6 == 0:
                    row = grid.row()
                    row.alignment = 'CENTER'

                row.template_icon(render.thumbnail_icon_id, scale=5)

        # material title
        row = col.row()
        row.alignment = 'CENTER'
        row.label(text=mat.title)

        # material description
        col = layout.column(align=True)
        if mat.description:
            for line in textwrap.wrap(mat.description, 60):
                col.label(text=line)

        col = layout.column(align=True)
        col.label(text=f"Category: {mat.category.title}")
        col.label(text=f"Author: {mat.author}")

        # packages
        package = matlib_prop.package
        if not package:
            return

        layout.prop(matlib_prop, 'package_id', icon='DOCUMENTS')

        row = layout.row()
        if package.has_file:
            row.operator(HDUSD_MATLIB_OP_import_material.bl_idname, icon='IMPORT')
        else:
            if package.size_load is None:
                row.operator(HDUSD_MATLIB_OP_load_package.bl_idname, icon='IMPORT')
            else:
                percent = min(100, int(package.size_load * 100 / package.size))
                row.operator(HDUSD_MATLIB_OP_load_package.bl_idname, icon='IMPORT',
                             text=f"Downloading Package...{percent}%")
                row.enabled = False


class HDUSD_MATLIB_PT_matlib_tools(HdUSD_Panel):
    bl_label = "Tools"
    bl_context = "material"
    bl_region_type = 'WINDOW'
    bl_parent_id = 'HDUSD_MATLIB_PT_matlib'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.label(text=manager.status)

        row = col.row()
        row.enabled = manager.is_synced
        row.operator(HDUSD_MATLIB_OP_load_materials.bl_idname, icon='FILE_REFRESH')
