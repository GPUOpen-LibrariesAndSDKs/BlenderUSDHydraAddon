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
from . import logging

from pxr import Usd
import RenderStudioKit

log = logging.Log("updates")


class RS_Resolver:
    _is_connected = False
    is_depsgraph_update = True
    usd_path = ''
    stage = None

    def get_resolver_path(self):
        path = ""
        if RenderStudioKit.IsUnresovableToRenderStudioPath(self.usd_path):
            path = RenderStudioKit.UnresolveToRenderStudioPath(self.usd_path)

        return path

    @property
    def is_connected(self):
        return self._is_connected

    @is_connected.setter
    def is_connected(self, value):
        self._is_connected = value
        self.update_button()

    def connect_server(self):
        from .import config
        info = RenderStudioKit.LiveSessionInfo(config.server_url, config.storage_url, config.channel_id, config.user_id)
        try:
            RenderStudioKit.LiveSessionConnect(info)
            self.is_connected = True

            log.debug("Connected: ", config.server_url, config.storage_url, config.channel_id, config.user_id)

        except Exception as err:
            log.error("Failed to connect: ", err)

    def connect(self):
        self.export_scene()
        self.open_usd()
        self.connect_server()

        if self.is_connected:
            self.sync()

    def disconnect(self):
        if self.is_connected:
            RenderStudioKit.LiveSessionDisconnect()
            self.is_connected = False
            self.stage = None
            self.usd_path = ''

        log.debug("Disconnected")

    def open_usd(self):
        path = self.get_resolver_path()
        if not path:
            log.debug("Failed to open stage: ", self.usd_path, path, self.stage)

        self.stage = Usd.Stage.Open(path)
        log.debug("Open stage: ", self.usd_path, path, self.stage)

    def export_scene(self):
        from . import config
        if not Path(self.usd_path).exists() or not self.usd_path:
            filename = bpy.path.ensure_ext(
                str(Path(f"{config.user_id}_{Path(bpy.data.filepath).stem}")), ".usda"
            )
            self.usd_path = str(config.render_studio_dir / filename)

        self.is_depsgraph_update = False
        log.debug("Export usd", self.usd_path)
        bpy.ops.wm.usd_export(filepath=self.usd_path)
        self.is_depsgraph_update = True

    def sync(self):
        res = False
        if self.is_connected:
            res = RenderStudioKit.LiveSessionUpdate()

        return res

    def on_depsgraph_update_post(self, scene, depsgraph):
        if not self.is_connected:
            return

        if not self.is_depsgraph_update:
            return

        self.export_scene()
        self.sync()

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
