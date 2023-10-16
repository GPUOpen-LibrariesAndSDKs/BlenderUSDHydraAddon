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

from pxr import Usd
import RenderStudioKit

from ..preferences import preferences

from .. import logging
log = logging.Log("rs.resolver")


class Resolver:
    def __init__(self):
        self.is_connected = False
        self.is_depsgraph_update = True
        self.usd_path = ""
        self.stage = None
        self.status = "Disconnected"
        self.is_exporting = False

    def connect(self):
        pref = preferences()
        RenderStudioKit.SetWorkspacePath(pref.rs_storage_dir)
        self.export_scene()

        if not RenderStudioKit.IsUnresovableToRenderStudioPath(self.usd_path):
            log.warn("No resolved path", self.usd_path)
            return

        uri_path = RenderStudioKit.UnresolveToRenderStudioPath(self.usd_path)

        log("Open stage", self.usd_path, uri_path)
        self.stage = Usd.Stage.Open(uri_path)
        if not self.stage:
            return

        log("Connect to server", pref.rs_server_url, pref.rs_storage_url, pref.rs_channel_id, pref.rs_user_id, pref.rs_storage_dir)
        info = RenderStudioKit.LiveSessionInfo(pref.rs_server_url, pref.rs_storage_url, pref.rs_channel_id, pref.rs_user_id)
        RenderStudioKit.LiveSessionConnect(info)
        self.is_connected = True
        self.status = "Connected"

        from .ui import update_button
        update_button()

    def disconnect(self):
        log("Disconnect server")

        RenderStudioKit.LiveSessionDisconnect()
        self.is_connected = False
        self.stage = None
        self.usd_path = ""
        self.status = "Disconnected"
        self.is_exporting = False

        from .ui import update_button
        update_button()

    def start_live_export(self):
        # TODO: Implement start live export
        self.is_exporting = True
        self.status = "Exporting..."

    def stop_live_export(self):
        # TODO: Implement stop live export
        self.is_exporting = False
        self.status = "Connected"

    def export_scene(self):
        pref = preferences()
        if not Path(self.usd_path).exists() or not self.usd_path:
            filename = bpy.path.ensure_ext(
                str(Path(f"{pref.rs_user_id}_{Path(bpy.data.filepath).stem}")), ".usda"
            )
            self.usd_path = str(Path(pref.rs_storage_dir) / filename)

        log("Exported scene", self.usd_path)

        self.is_depsgraph_update = False
        bpy.ops.wm.usd_export(filepath=self.usd_path)
        self.status = "Exported"
        self.is_depsgraph_update = True


rs_resolver = Resolver()


def on_depsgraph_update_post(scene, depsgraph):
    if not rs_resolver.is_connected or not rs_resolver.is_depsgraph_update:
        return

    rs_resolver.export_scene()


def register():
    bpy.app.handlers.depsgraph_update_post.append(on_depsgraph_update_post)


def unregister():
    if on_depsgraph_update_post in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(on_depsgraph_update_post)

    if rs_resolver.is_connected:
        rs_resolver.disconnect()
