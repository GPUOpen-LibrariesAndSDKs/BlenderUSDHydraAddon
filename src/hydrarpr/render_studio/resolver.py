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
        self.status = "Disconnected"
        self.is_syncing = False

    def connect(self):
        pref = preferences()
        RenderStudioKit.SetWorkspacePath(pref.rs_storage_dir)
        RenderStudioKit.SharedWorkspaceConnect()
        self.is_connected = True
        self.status = "Connected"

        from .ui import update_button
        update_button()

    def disconnect(self):
        log("Disconnect server")

        RenderStudioKit.SharedWorkspaceDisconnect()
        self.is_connected = False
        self.status = "Disconnected"
        self.is_syncing = False

        from .ui import update_button
        update_button()

    def start_live_sync(self):
        # TODO: Implement start live sync
        self.is_syncing = True
        self.status = "Syncing..."

    def stop_live_sync(self):
        # TODO: Implement stop live sync
        self.is_syncing = False
        self.status = "Connected"

    def sync_scene(self):
        pref = preferences()
        usd_path = Path(pref.rs_storage_dir) / f"{pref.rs_user_id}_{Path(bpy.data.filepath).stem}.usdc"

        log("Syncing scene", usd_path)
        self.is_depsgraph_update = False
        try:
            bpy.ops.wm.usd_export(filepath=str(usd_path))
            self.status = "Synced"

        finally:
            self.is_depsgraph_update = True


rs_resolver = Resolver()


def on_depsgraph_update_post(scene, depsgraph):
    if not rs_resolver.is_connected or not rs_resolver.is_depsgraph_update:
        return

    rs_resolver.sync_scene()


def register():
    bpy.app.handlers.depsgraph_update_post.append(on_depsgraph_update_post)


def unregister():
    if on_depsgraph_update_post in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(on_depsgraph_update_post)

    if rs_resolver.is_connected:
        rs_resolver.disconnect()
