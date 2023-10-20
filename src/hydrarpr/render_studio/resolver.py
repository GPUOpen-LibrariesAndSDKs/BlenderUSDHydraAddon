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
from pathlib import Path

import bpy

from rs import RenderStudioKit

from ..preferences import preferences

from .. import logging
log = logging.Log("rs.resolver")


class Resolver:
    def __init__(self):
        self.is_connected = False
        self.is_depsgraph_update = True
        self.is_syncing = False
        self.filename = ""

    def connect(self):
        pref = preferences()
        if not pref.rs_workspace_url:
            log("Remote server URL is empty")
            return

        RenderStudioKit.SetWorkspaceUrl(pref.rs_workspace_url)
        RenderStudioKit.SetWorkspacePath(pref.rs_workspace_dir)

        try:
            RenderStudioKit.SharedWorkspaceConnect()
            self.is_connected = True

        except RuntimeError:
            log("Failed connect to remote server", pref.rs_workspace_url)

        from .ui import update_button
        update_button()

    def disconnect(self):
        log("Disconnect server")

        RenderStudioKit.SharedWorkspaceDisconnect()
        self.is_connected = False
        self.is_syncing = False
        self.filename = ""

        from .ui import update_button
        update_button()

    def start_live_sync(self):
        bpy.app.handlers.depsgraph_update_post.append(on_depsgraph_update_post)
        self.is_syncing = True

    def stop_live_sync(self):
        bpy.app.handlers.depsgraph_update_post.remove(on_depsgraph_update_post)
        self.is_syncing = False

    def sync_scene(self):
        pref = preferences()
        settings = bpy.context.scene.hydra_rpr.render_studio
        self.filename = Path(bpy.data.filepath).stem if bpy.data.filepath else "untitled"
        self.filename += pref.rs_file_format
        usd_path = Path(pref.rs_workspace_dir) / settings.channel / self.filename

        log("Syncing scene", usd_path)
        self.is_depsgraph_update = False
        try:
            bpy.ops.wm.usd_export(
                filepath=str(usd_path),
                selected_objects_only=settings.selected_objects_only,
                visible_objects_only=settings.visible_objects_only,
                export_animation=settings.export_animation,
                export_hair=settings.export_hair,
                export_normals=settings.export_normals,
                export_materials=settings.export_materials,
                use_instancing=settings.use_instancing,
                evaluation_mode=settings.evaluation_mode,
                generate_preview_surface=settings.generate_preview_surface,
                export_textures=settings.export_textures,
                overwrite_textures=settings.overwrite_textures,
                root_prim_path=settings.root_prim_path,
            )
        finally:
            self.is_depsgraph_update = True


rs_resolver = Resolver()


def on_depsgraph_update_post(scene, depsgraph):
    if not rs_resolver.is_connected or not rs_resolver.is_depsgraph_update or not rs_resolver.is_syncing:
        return

    rs_resolver.sync_scene()


def unregister():
    if rs_resolver.is_syncing:
        rs_resolver.stop_live_sync()

    if rs_resolver.is_connected:
        rs_resolver.disconnect()
