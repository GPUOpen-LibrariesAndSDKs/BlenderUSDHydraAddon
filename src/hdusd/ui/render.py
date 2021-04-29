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

from . import HdUSD_Panel


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


class HDUSD_MT_data_source_final(DataSourceMenu):
    """Select data source"""
    bl_idname = "HDUSD_MT_data_source_final"
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


class HDUSD_RENDER_PT_render_settings_final(RenderSettingsPanel):
    """Final render delegate and settings"""
    bl_label = "Final Render Settings"
    engine_type = 'FINAL'


class HDUSD_RENDER_PT_render_settings_viewport(RenderSettingsPanel):
    """Viewport render delegate and settings"""
    bl_label = "Viewport Render Settings"
    engine_type = 'VIEWPORT'


class HDUSD_RENDER_PT_debug(HdUSD_Panel):
    bl_label = "Debug"
    bl_context = 'render'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene.hdusd, "rpr_viewport_cpu_device")
        layout.prop(context.scene.hdusd, "use_rpr_mx_nodes")
