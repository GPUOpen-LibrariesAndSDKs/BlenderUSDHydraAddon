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
    bl_label = "AMD RenderStudio"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.hydra_rpr.render_studio
        if rs_resolver.is_connected:
            layout.operator("render_studio.disconnect", icon='UNLINKED')

        else:
            layout.operator("render_studio.connect", icon='LINKED')

        col = layout.column()
        col.enabled = rs_resolver.is_connected
        col.separator()

        col = col.column()
        if settings.live_sync:
            if rs_resolver.is_syncing:
                col.operator("render_studio.stop_live_sync", icon='CANCEL')
            else:
                col.operator("render_studio.start_live_sync", icon='FILE_REFRESH')
        else:
            col.operator("render_studio.sync_scene", icon='FILE_REFRESH')

        col.prop(settings, "live_sync")
        col.separator()
        layout.label(text=f"Status: {rs_resolver.status}")


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


def register():
    bpy.utils.register_class(RS_RESOLVER_PT_resolver)


def unregister():
    bpy.utils.unregister_class(RS_RESOLVER_PT_resolver)
