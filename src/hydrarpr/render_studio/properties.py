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
from RenderStudioResolver import RenderStudioResolver, LiveModeInfo

from .. import logging
log = logging.Log("rs.operators")


stage_cache = Usd.StageCache()


class RESOLVER_collection_properties(bpy.types.PropertyGroup):
    stageId: bpy.props.IntProperty(
        name="Stage Id",
        default=-1,
        )
    usd_path: bpy.props.StringProperty(
        subtype='FILE_PATH',
        name="USD Stage",
        default=""
        )
    is_connected: bpy.props.BoolProperty(
        name="Is Live Mode",
        default=False
        )
    is_depsgraph_update: bpy.props.BoolProperty(
        name="Is Depsgraph Update",
        description="",
        default=True
        )

    def get_resolver_path(self):
        path = self.usd_path
        if not RenderStudioResolver.IsRenderStudioPath(path):
            if RenderStudioResolver.IsUnresovableToRenderStudioPath(path):
                path = RenderStudioResolver.Unresolve(path)
            else:
                return False
        log.debug("Resolved Path: ", path)
        return path

    def connect_server(self):
        from .import config
        info = LiveModeInfo(config.server_url, config.storage_url, config.channel_id, config.user_id)
        try:
            RenderStudioResolver.StartLiveMode(info)
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
        RenderStudioResolver.StopLiveMode()
        self.is_connected = False

        log.debug("Disconnected")

    def get_stage(self):
        stage = stage_cache.Find(Usd.StageCache.Id.FromLongInt(self.stageId))

        log.debug("Stage: ", stage)
        return stage

    def open_usd(self):
        path = self.get_resolver_path()
        stage = Usd.Stage.Open(path)
        self.stageId = stage_cache.Insert(stage).ToLongInt()

        log.debug("Open stage: ", self.usd_path, path, stage)
        return stage

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
            res = RenderStudioResolver.ProcessLiveUpdates()

        return res


def register():
    bpy.utils.register_class(RESOLVER_collection_properties)
    bpy.types.Collection.resolver = bpy.props.PointerProperty(type=RESOLVER_collection_properties)


def unregister():
    bpy.utils.unregister_class(RESOLVER_collection_properties)
    del bpy.types.Collection.resolver
