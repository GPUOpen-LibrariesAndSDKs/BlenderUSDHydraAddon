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
from .. import config

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

    @classmethod
    def poll(cls, context):
        return super().poll(context) and config.matlib_enabled

    def draw(self, context):
        layout = self.layout
        matlib_prop = context.window_manager.hdusd.matlib

        layout.prop(matlib_prop, "category")
        layout.template_icon_view(matlib_prop, "material")

        row = layout.row()
        row.enabled = bool(context.material)
        row.operator(HDUSD_MATLIB_OP_import_material.bl_idname)

        split = layout.row(align=True).split(factor=0.4)
        col = split.column()
        col.alignment = 'LEFT'
        col.label(text="Package")
        col = split.column()

        matlib_prop = context.window_manager.hdusd.matlib

        if matlib_prop.material:
            packages = matlib_prop.pcoll.materials[matlib_prop.material].packages
            package = None

            if matlib_prop.package_id:
                # TODO maybe need to find a better way than try/except but it's too late now
                try:
                    package = next(package for package in packages
                                   if package.id == matlib_prop.package_id)
                except:
                    package = packages[0]
            else:
                package = packages[0]

            if package is not None and package.file is None:
                package.get_info()

            col.menu(HDUSD_MATLIB_MT_package_menu.bl_idname,
                     text=package.label + "size=" + package.size if package is not None else None,
                     icon='DOCUMENTS')


class HDUSD_MATLIB_MT_package_menu(bpy.types.Menu):
    bl_label = "Package"
    bl_idname = "HDUSD_MATLIB_MT_package_menu"

    def draw(self, context):
        layout = self.layout
        op_idname = HDUSD_MATLIB_OP_select_package.bl_idname

        matlib_prop = context.window_manager.hdusd.matlib
        packages = matlib_prop.pcoll.materials[matlib_prop.material].packages

        for package in packages:
            if package.file is None:
                package.get_info()

            row = layout.row()
            op = row.operator(op_idname, text=package.label + "  s ize=" + package.size,
                              icon='DOCUMENTS')
            op.matlib_package_id = package.id


class HDUSD_MATLIB_OP_select_package(bpy.types.Operator):
    """Select Package"""
    bl_label = "Select Package"
    bl_idname = "hdusd.matlib_select_package"

    matlib_package_id: bpy.props.StringProperty(default="")

    def execute(self, context):
        context.window_manager.hdusd.matlib.package_id = self.matlib_package_id
        return {"FINISHED"}
