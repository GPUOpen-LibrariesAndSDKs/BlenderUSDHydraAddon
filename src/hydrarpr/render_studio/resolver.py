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

from ..preferences import preferences

from .. import logging
log = logging.Log("rs.resolver")


class Resolver:
    def __init__(self):
        self.is_connected = False
        self.is_live_sync = False
        self.filename = ""

        self._is_depsgraph_update = False

    def connect(self):
        from rs import RenderStudioKit

        log("Connecting")
        pref = preferences()
        RenderStudioKit.SetWorkspacePath(pref.rs_storage_dir)
        RenderStudioKit.SharedWorkspaceConnect()
        self.is_connected = True
        log.info("Connected")

        from . import ui
        ui.tag_redraw()

    def disconnect(self):
        from rs import RenderStudioKit

        if self.is_live_sync:
            self.stop_live_sync()

        log("Disconnecting")
        RenderStudioKit.SharedWorkspaceDisconnect()
        self.is_connected = False
        self.filename = ""
        log.info("Disconnected")

        from . import ui
        ui.tag_redraw()

    def start_live_sync(self):
        log("Start live sync")
        bpy.app.handlers.depsgraph_update_post.append(on_depsgraph_update_post)
        self.is_live_sync = True

    def stop_live_sync(self):
        log("Stop live sync")
        bpy.app.handlers.depsgraph_update_post.remove(on_depsgraph_update_post)
        self.is_live_sync = False

    def sync_scene(self):
        if self._is_depsgraph_update:
            return

        pref = preferences()
        settings = bpy.context.scene.hydra_rpr.render_studio

        self.filename = Path(bpy.data.filepath).stem if bpy.data.filepath else "untitled"
        self.filename += pref.rs_file_format
        usd_path = Path(pref.rs_storage_dir) / settings.channel / self.filename

        log("Syncing scene", usd_path)
        self._is_depsgraph_update = True
        try:
            bpy.ops.wm.usd_export(
                filepath=str(usd_path),
                selected_objects_only=settings.selected_objects_only,
                visible_objects_only=settings.visible_objects_only,
                export_animation=settings.export_animation,
                export_hair=settings.export_hair,
                # export_mesh_colors=settings.export_mesh_colors,
                export_normals=settings.export_normals,
                export_materials=settings.export_materials,
                use_instancing=settings.use_instancing,
                evaluation_mode=settings.evaluation_mode,
                generate_preview_surface=settings.generate_preview_surface,
                export_textures=settings.export_textures,
                overwrite_textures=settings.overwrite_textures,
                relative_paths=settings.relative_paths,
                root_prim_path=settings.root_prim_path,
            )
        finally:
            self._is_depsgraph_update = False


rs_resolver = Resolver()


def on_depsgraph_update_post(scene, depsgraph):
    rs_resolver.sync_scene()
