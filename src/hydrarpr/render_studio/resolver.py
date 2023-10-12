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


class RS_Resolver:
    is_connected = False
    is_depsgraph_update = True
    usd_path = ""
    stage = None

    def get_resolved_path(self):
        path = ""
        if RenderStudioKit.IsUnresovableToRenderStudioPath(self.usd_path):
            path = RenderStudioKit.UnresolveToRenderStudioPath(self.usd_path)

        return path

    def update_usd_path(self):
        if not Path(self.usd_path).exists() or not self.usd_path:
            filename = bpy.path.ensure_ext(
                str(Path(f"{USER_ID}_{Path(bpy.data.filepath).stem}")), ".usda"
            )
            self.usd_path = str(STORAGE_DIR / filename)

        return self.usd_path

    def connect(self):
        self.set_storage_dir(str(STORAGE_DIR))
        self.export_scene()
        self.open_usd()

        if self.stage:
            self.connect_server()

    def connect_server(self):
        log("Connect to server :", SERVER_URL, STORAGE_URL, CHANNEL_ID, USER_ID, STORAGE_DIR)

        info = RenderStudioKit.LiveSessionInfo(SERVER_URL, STORAGE_URL, CHANNEL_ID, USER_ID)
        RenderStudioKit.LiveSessionConnect(info)
        self.is_connected = True
        self.update_button()

    def disconnect(self):
        log("Disconnect server")

        RenderStudioKit.LiveSessionDisconnect()
        self.is_connected = False
        self.stage = None
        self.usd_path = ""
        self.update_button()

    def open_usd(self):
        path = self.get_resolved_path()
        log("Opened stage: ", self.usd_path, path)

        if path:
            self.stage = Usd.Stage.Open(path)

        else:
            log("Failed to open stage: ", self.usd_path, path)

    def export_scene(self):
        self.update_usd_path()
        log("Exported scene", self.usd_path)

        self.is_depsgraph_update = False
        bpy.ops.wm.usd_export(filepath=self.usd_path)
        self.is_depsgraph_update = True

    def on_depsgraph_update_post(self, scene, depsgraph):
        if not self.is_connected:
            return

        if not self.is_depsgraph_update:
            return

        self.export_scene()

    @staticmethod
    def set_storage_dir(dir_path):
        RenderStudioKit.SetWorkspacePath(dir_path)

    @staticmethod
    def update_button():
        for window in bpy.context.window_manager.windows:
            for area in window.screen.areas:
                if area.type in ['PROPERTIES', 'OUTLINER']:
                    for region in area.regions:
                        if ((area.type == 'PROPERTIES' and region.type == 'WINDOW') or
                                (area.type == 'OUTLINER' and region.type == 'HEADER')):
                            region.tag_redraw()


rs_resolver = RS_Resolver()


def register():
    bpy.app.handlers.depsgraph_update_post.append(rs_resolver.on_depsgraph_update_post)


def unregister():
    if rs_resolver.on_depsgraph_update_post in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(rs_resolver.on_depsgraph_update_post)

    if rs_resolver.is_connected:
        rs_resolver.disconnect()
