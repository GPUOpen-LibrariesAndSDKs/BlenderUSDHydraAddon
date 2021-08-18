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
import webbrowser

from . import HdUSD_Panel, HdUSD_Operator

from hdusd import bl_info

from pxr import UsdAppUtils, Tf

from rpr import RprUsd

class HDUSD_OP_open_web_page(HdUSD_Operator):
    """
    Operator to open web pages. Available page types:
    - 'main_site'
    - 'documentation'
    - 'downloads'
    - 'community'
    - 'bug_reports'
    """

    bl_idname = "hdusd.op_open_web_page"
    bl_label = "Open Web Page"
    bl_description = "Open web page in browser"

    page: bpy.props.StringProperty(name="Page")

    def execute(self, context):
        url = {
            'main_site':     "https://www.amd.com/en/technologies/radeon-prorender",
            'documentation': "https://radeon-pro.github.io/RadeonProRenderDocs/en/usd_hydra/about.html",
            'downloads':     "https://www.amd.com/en/technologies/radeon-prorender-downloads",
            'community':     "https://github.com/GPUOpen-LibrariesAndSDKs/BlenderUSDHydraAddon/discussions",
            'bug_reports':   "https://github.com/GPUOpen-LibrariesAndSDKs/BlenderUSDHydraAddon/issues",
        }[self.page]

        webbrowser.open(url)
        return {'FINISHED'}


class HDUSD_OP_data_source(bpy.types.Operator):
    """Select render source"""
    bl_idname = "hdusd.data_source"
    bl_label = "Data Source"

    data_source: bpy.props.StringProperty(default="")
    engine_type: bpy.props.EnumProperty(
        items=(('FINAL', "Final", "For final render"),
               ('VIEWPORT', "Viewport", "For viewport render")),
        default='FINAL'
    )

    def execute(self, context):
        settings = context.scene.hdusd.final if self.engine_type == 'FINAL' else\
                   context.scene.hdusd.viewport
        settings.data_source = self.data_source

        context.scene.hdusd.final.nodetree_update(context)

        return {"FINISHED"}


class HDUSD_OP_nodetree_camera(bpy.types.Operator):
    """Select camera"""
    bl_idname = "hdusd.nodetree_camera"
    bl_label = "Camera"

    nodetree_camera: bpy.props.StringProperty(default="")

    def execute(self, context):
        settings = context.scene.hdusd.final
        settings.nodetree_camera = self.nodetree_camera
        return {"FINISHED"}


class DataSourceMenu(bpy.types.Menu):
    bl_label = "Data Source"
    engine_type = None

    def draw(self, context):
        layout = self.layout
        node_groups = bpy.data.node_groups
        op_idname = HDUSD_OP_data_source.bl_idname

        op = layout.operator(op_idname, text=context.scene.name, icon='SCENE_DATA')
        op.data_source = ""
        op.engine_type = self.engine_type

        for ng in node_groups:
            if ng.bl_idname != 'hdusd.USDTree':
                continue

            row = layout.row()
            row.enabled = bool(ng.get_output_node())
            op = row.operator(op_idname, text=ng.name, icon='NODETREE')
            op.data_source = ng.name
            op.engine_type = self.engine_type


class NodetreeCameraMenu(bpy.types.Menu):
    bl_label = "Camera"

    def draw(self, context):
        layout = self.layout
        node_groups = bpy.data.node_groups
        op_idname = HDUSD_OP_nodetree_camera.bl_idname
        settings = context.scene.hdusd.final
        ng = bpy.data.node_groups[settings.data_source]

        output_node = ng.get_output_node()
        if output_node is None:
            return

        stage = output_node.cached_stage()
        if stage is None:
            return

        for prim in stage.TraverseAll():
            if prim.GetTypeName() == 'Camera':
                row = layout.row()
                op = row.operator(op_idname, text=prim.GetPath().pathString)
                op.nodetree_camera = prim.GetPath().pathString


class HDUSD_MT_data_source_final(DataSourceMenu):
    """Select data source"""
    bl_idname = "HDUSD_MT_data_source_final"
    engine_type = 'FINAL'


class HDUSD_MT_nodetree_camera_final(NodetreeCameraMenu):
    """Select camera"""
    bl_idname = "HDUSD_MT_nodetree_camera_final"
    engine_type = 'FINAL'


class HDUSD_MT_data_source_viewport(DataSourceMenu):
    """Select render source"""
    bl_idname = "HDUSD_MT_data_source_viewport"
    engine_type = 'VIEWPORT'


class RenderSettingsPanel(HdUSD_Panel):
    bl_context = 'render'
    engine_type = None

    def draw(self, context):
        scene = context.scene
        settings = scene.hdusd.final if self.engine_type == 'FINAL' else scene.hdusd.viewport

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.prop(settings, "delegate")

        split = layout.row(align=True).split(factor=0.4)
        col = split.column()
        col.alignment = 'RIGHT'
        col.label(text="Data Source")
        col = split.column()
        col.menu(HDUSD_MT_data_source_final.bl_idname if self.engine_type == 'FINAL' else
                 HDUSD_MT_data_source_viewport.bl_idname,
                 text=settings.data_source if settings.data_source else scene.name,
                 icon='NODETREE' if settings.data_source else 'SCENE_DATA')

        if self.engine_type == 'FINAL' and settings.data_source:
            split = layout.row(align=True).split(factor=0.4)
            col = split.column()
            col.alignment = 'RIGHT'
            col.label(text="Camera")
            col = split.column()
            col.enabled = settings.nodetree_camera != ''
            col.menu(HDUSD_MT_nodetree_camera_final.bl_idname,
                     text=settings.nodetree_camera if settings.nodetree_camera else '')


class HDUSD_RENDER_PT_render_settings_final(RenderSettingsPanel):
    """Final render delegate and settings"""
    bl_label = "Final Render Settings"
    engine_type = 'FINAL'


class HDUSD_RENDER_PT_render_settings_viewport(RenderSettingsPanel):
    """Viewport render delegate and settings"""
    bl_label = "Viewport Render Settings"
    engine_type = 'VIEWPORT'


class HDUSD_RENDER_PT_help_about(HdUSD_Panel):
    """Help/About UI panel"""

    bl_label = "Help/About"
    bl_context = 'render'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        def label_center(lay, text):
            row = lay.row()
            row.alignment = 'CENTER'
            row.label(text=text)

        layout = self.layout

        # Drawing info about plugin
        col = layout.column(align=True)
        version = bl_info['version']
        label_center(col, f"{bl_info['name']} for Blender {version[0]}.{version[1]}.{version[2]}")
        label_center(col, "© 2021 Advanced Micro Devices, Inc. (AMD)")
        label_center(col, "Portions of this software are created")
        label_center(col, "and copyrighted to other third parties.")

        # Drawing buttons to open web pages
        layout.separator()
        col = layout.column()
        row = col.row(align=True)
        row.alignment = 'CENTER'
        row.operator('hdusd.op_open_web_page', text="Main Site").page = 'main_site'
        row.operator('hdusd.op_open_web_page', text="Documentation").page = 'documentation'
        row.operator('hdusd.op_open_web_page', text="Downloads").page = 'downloads'

        row = col.row(align=True)
        row.alignment = 'CENTER'
        row.operator('hdusd.op_open_web_page', text="Community").page = 'community'
        row.operator('hdusd.op_open_web_page', text="Bug Reports").page = 'bug_reports'


class HDUSD_RENDER_PT_debug(HdUSD_Panel):
    bl_label = "Debug"
    bl_context = 'render'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene.hdusd, "use_rpr_mx_nodes")
