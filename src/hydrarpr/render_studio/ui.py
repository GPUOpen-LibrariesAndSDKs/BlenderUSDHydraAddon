# **********************************************************************
# Copyright 2023 Advanced Micro Devices, Inc
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
# ********************************************************************
import bpy

from .resolver import rs_resolver
from ..ui import Panel


class RS_RESOLVER_PT_resolver(Panel):
    bl_idname = 'RS_RESOLVER_PT_resolver'
    bl_label = "AMD RenderStudio"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        settings = context.scene.hydra_rpr.render_studio
        if rs_resolver.is_connected:
            layout.operator("render_studio.disconnect", icon='UNLINKED')
        else:
            layout.operator("render_studio.connect", icon='LINKED')

        col = layout.column()
        col.enabled = rs_resolver.is_connected
        col.separator()

        col1 = col.column(align=True)
        col1.use_property_split = False
        if settings.live_sync:
            if rs_resolver.is_live_sync:
                col1.operator("render_studio.stop_live_sync", icon='CANCEL')
            else:
                col1.operator("render_studio.start_live_sync", icon='FILE_REFRESH')
        else:
            col1.operator("render_studio.sync_scene", icon='FILE_REFRESH')

        col1.prop(settings, "live_sync")

        col.separator()
        col.prop(settings, "channel")

        if rs_resolver.filename:
            col1 = col.column(align=True)
            col1.label(text="Syncing to:")
            col1.label(text=f"{settings.channel}/{rs_resolver.filename}")


class RS_RESOLVER_PT_usd_settings(Panel):
    bl_parent_id = RS_RESOLVER_PT_resolver.bl_idname
    bl_label = "USD Settings"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        settings = context.scene.hydra_rpr.render_studio

        col = layout.column()
        col.enabled = rs_resolver.is_connected
        col.separator()

        col.prop(settings, "selected_objects_only")
        col.prop(settings, "visible_objects_only")
        col.prop(settings, "export_animation")
        col.prop(settings, "export_hair")
        col.prop(settings, "export_uvmaps")
        col.prop(settings, "export_normals")
        col.prop(settings, "export_materials")
        col.prop(settings, "root_prim_path")
        col.prop(settings, "evaluation_mode")
        col.separator()

        col1 = col.column()
        col1.enabled = settings.export_materials
        col1.prop(settings, "generate_preview_surface")
        col1.prop(settings, "export_textures")
        col1.prop(settings, "overwrite_textures")
        col.separator()

        col.prop(settings, "relative_paths")
        col.separator()

        col.prop(settings, "use_instancing")


def draw_button(self, context):
    if rs_resolver.is_connected:
        self.layout.operator("render_studio.disconnect", icon='UNLINKED')

    else:
        self.layout.operator("render_studio.connect", icon='LINKED')


def update_button():
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type in ['PROPERTIES', 'OUTLINER']:
                for region in area.regions:
                    if area.type == 'PROPERTIES' and region.type == 'WINDOW':
                        region.tag_redraw()


register, unregister = bpy.utils.register_classes_factory((
    RS_RESOLVER_PT_resolver,
    RS_RESOLVER_PT_usd_settings,
))
