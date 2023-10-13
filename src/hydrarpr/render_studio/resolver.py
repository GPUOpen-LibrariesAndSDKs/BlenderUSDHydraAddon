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
import uuid
from pathlib import Path

import bpy

from pxr import Usd
import RenderStudioKit

from .. import logging
log = logging.Log("rs.resolver")


STORAGE_DIR = Path.home() / "AppData/Roaming/AMDRenderStudio/Storage/.storage/workspace"
USER_ID = f"BlenderUser_{uuid.uuid4()}"
SERVER_URL = ""
STORAGE_URL = ""
CHANNEL_ID = "Blender"


class Resolver:
    def __init__(self):
        self.is_connected = False
        self.is_depsgraph_update = True
        self.usd_path = ""
        self.stage = None

    def get_resolved_path(self):
        if not RenderStudioKit.IsUnresovableToRenderStudioPath(self.usd_path):
            return ""

        return RenderStudioKit.UnresolveToRenderStudioPath(self.usd_path)

    def connect(self):
        self.export_scene()

        path = self.get_resolved_path()
        if not path:
            log.warn("Failed to : ", self.usd_path, path)
            return

        self.stage = Usd.Stage.Open(path)
        log("Opened stage: ", self.usd_path, path)

        if not self.stage:
            return

        log("Connect to server :", SERVER_URL, STORAGE_URL, CHANNEL_ID, USER_ID, STORAGE_DIR)

        info = RenderStudioKit.LiveSessionInfo(SERVER_URL, STORAGE_URL, CHANNEL_ID, USER_ID)
        RenderStudioKit.LiveSessionConnect(info)
        self.is_connected = True

        from .ui import update_button
        update_button()

    def disconnect(self):
        log("Disconnect server")

        RenderStudioKit.LiveSessionDisconnect()
        self.is_connected = False
        self.stage = None
        self.usd_path = ""

        from .ui import update_button
        update_button()

    def export_scene(self):
        if not Path(self.usd_path).exists() or not self.usd_path:
            filename = bpy.path.ensure_ext(
                str(Path(f"{USER_ID}_{Path(bpy.data.filepath).stem}")), ".usda"
            )
            self.usd_path = str(STORAGE_DIR / filename)

        log("Exported scene", self.usd_path)

        self.is_depsgraph_update = False
        bpy.ops.wm.usd_export(filepath=self.usd_path)
        self.is_depsgraph_update = True


rs_resolver = Resolver()


def on_depsgraph_update_post(scene, depsgraph):
    if not rs_resolver.is_connected:
        return

    if not rs_resolver.is_depsgraph_update:
        return

    rs_resolver.export_scene()


def register():
    RenderStudioKit.SetWorkspacePath(str(STORAGE_DIR))

    bpy.app.handlers.depsgraph_update_post.append(on_depsgraph_update_post)


def unregister():
    if on_depsgraph_update_post in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(on_depsgraph_update_post)

    if rs_resolver.is_connected:
        rs_resolver.disconnect()
