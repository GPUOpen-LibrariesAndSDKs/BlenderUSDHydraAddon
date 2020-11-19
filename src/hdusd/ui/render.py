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
from ..usd_nodes.node_tree import get_usd_nodetree


class HDUSD_OP_render_source_select(bpy.types.Operator):
    """Select render source"""
    bl_idname = "hdusd.render_source_select"
    bl_label = "Render Source"

    source_name: bpy.props.StringProperty(default="")

    def execute(self, context):
        context.scene.hdusd.source_name = self.source_name
        return {"FINISHED"}


class HDUSD_MT_render_source(bpy.types.Menu):
    """Select render source"""
    bl_idname = "HDUSD_MT_render_source"
    bl_label = "Render Source"

    def draw(self, context):
        layout = self.layout
        node_groups = bpy.data.node_groups
        op_idname = HDUSD_OP_render_source_select.bl_idname

        layout.operator(op_idname, text=context.scene.name, icon='SCENE_DATA').source_name = ""
        for ng in node_groups:
            if ng.bl_idname != 'hdusd.USDTree':
                continue

            row = layout.row()
            row.operator(op_idname, text=ng.name, icon='NODETREE').source_name = ng.name
            row.enabled = ng.get_output_node() is not None


class HDUSD_RENDER_PT_delegate_final(HdUSD_Panel):
    """
    Final Render Delegate and settings
    """
    bl_label = "Final Renderer"
    bl_context = 'render'

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        scene = context.scene
        layout.prop(scene.hdusd.final, "delegate")

        # use the USD nodegraph if present
        row = layout.row()
        row.prop(scene.hdusd.final, "use_usd_nodegraph")
        row.enabled = get_usd_nodetree() is not None

        row = layout.row()
        col = row.column()
        col.alignment = 'RIGHT'
        col.label(text="Render Source")
        col = row.column()
        col.menu(HDUSD_MT_render_source.bl_idname,
                 text=scene.hdusd.source_name if scene.hdusd.source_name else scene.name,
                 icon='NODETREE' if scene.hdusd.source_name else 'SCENE_DATA')


class HDUSD_RENDER_PT_delegate_viewport(HdUSD_Panel):
    """
    Viewport Render Delegate and settings
    """
    bl_label = "Viewport Renderer"
    bl_context = 'render'

    def draw(self, context):
        from ..usd_nodes.node_tree import get_usd_nodetree

        layout = self.layout

        scene = context.scene
        layout.prop(scene.hdusd.viewport, "delegate")

        # use the USD nodegraph if present
        row = layout.row()
        row.prop(scene.hdusd.viewport, "use_usd_nodegraph")
        row.enabled = get_usd_nodetree() is not None
