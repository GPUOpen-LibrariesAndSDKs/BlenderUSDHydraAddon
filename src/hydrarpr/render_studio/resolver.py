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
from pxr import Tf

from ..preferences import preferences

from .. import logging
log = logging.Log("rs.resolver")


class Resolver:
    def __init__(self):
        self.is_connected = False
        self.filename = ""
        self._connection_listener = Tf.Notice.RegisterGlobally(
            "RenderStudioNotice::WorkspaceConnectionChanged", self._connection_callback)

        self._is_depsgraph_update = False

    @property
    def is_live_sync(self):
        return on_depsgraph_update_post in bpy.app.handlers.depsgraph_update_post

    def _connection_callback(self, notice, sender):
        from .ui import tag_redraw

        self.is_connected = notice.IsConnected()
        log("RenderStudioNotice::WorkspaceConnectionChanged", notice.IsConnected())
        tag_redraw()

    def connect(self):
        from rs import RenderStudioKit

        log("Connecting")
        pref = preferences()
        RenderStudioKit.SetWorkspaceUrl(pref.rs_workspace_url)
        # RenderStudioKit.SetWorkspacePath(pref.rs_workspace_dir)

        try:
            RenderStudioKit.SharedWorkspaceConnect(RenderStudioKit.Role.Client)
            log.info("Connected")

        except RuntimeError:
            log.error("Failed connect to remote server", pref.rs_workspace_url)

    def disconnect(self):
        from rs import RenderStudioKit

        if self.is_live_sync:
            self.stop_live_sync()

        log("Disconnecting")
        RenderStudioKit.SharedWorkspaceDisconnect()
        self.filename = ""
        log.info("Disconnected")

    def start_live_sync(self):
        log("Start live sync")
        bpy.app.handlers.depsgraph_update_post.append(on_depsgraph_update_post)

    def stop_live_sync(self):
        log("Stop live sync")
        bpy.app.handlers.depsgraph_update_post.remove(on_depsgraph_update_post)

    def sync_scene(self):
        if self._is_depsgraph_update:
            return

        from rs import RenderStudioKit

        pref = preferences()
        settings = bpy.context.scene.hydra_rpr.render_studio

        self.filename = Path(bpy.data.filepath).stem if bpy.data.filepath else "untitled"
        self.filename += pref.rs_file_format
        usd_path = Path(RenderStudioKit.GetWorkspacePath()) / settings.channel / self.filename

        log("Syncing scene", usd_path)
        self._is_depsgraph_update = True
        USDSyncHook.enable()
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
            USDSyncHook.disable()
            self._is_depsgraph_update = False


class USDSyncHook(bpy.types.USDHook):
    bl_idname = "usd_sync_hook"
    bl_label = "USD Sync Hook"

    @staticmethod
    def on_export(export_context):
        stage = export_context.get_stage()
        if not stage:
            return False

        from . import world
        settings = bpy.context.scene.hydra_rpr.render_studio
        try:
            log("Exporting World")
            if settings.export_world:
                world.sync(stage, export_context.get_depsgraph())

        except Exception as err:
            log.error("Can't sync World", err)
            return False

        return True

    @classmethod
    def enable(cls):
        bpy.utils.register_class(cls)

    @classmethod
    def disable(cls):
        bpy.utils.unregister_class(cls)


rs_resolver = Resolver()


def on_depsgraph_update_post(scene, depsgraph):
    rs_resolver.sync_scene()
