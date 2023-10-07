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
import bpy
import mathutils
from threading import Thread
from pxr import Usd, UsdGeom
from . import logging
from RenderStudioResolver import RenderStudioResolver, LiveModeInfo

log = logging.Log("operators")
stage_cache = Usd.StageCache()


class RESOLVER_object_properties(bpy.types.PropertyGroup):
    sdf_path: bpy.props.StringProperty(
        name="Sdf Path",
        description="",
        default='',
        )


class RESOLVER_collection_properties(bpy.types.PropertyGroup):
    liveUrl: bpy.props.StringProperty(
        name="Live Url",
        description="",
        default='',
    )
    storageUrl: bpy.props.StringProperty(
        name="Storage Url",
        description="",
        default='',
        )
    channelId: bpy.props.EnumProperty(
        name="Channel Id",
        items=(
            ('BLENDER', "Blender", "Blender", 0),
            ('MAYA', "Maya", "Maya", 1),
            ('RENDERSTUDIO', "RenderStudio", "RenderStudio", 2),
            ),
        default=0,
        )
    userId: bpy.props.StringProperty(
        name="User Id",
        default='BlenderUser',
        )

    stageId: bpy.props.IntProperty(
        name="Stage Id",
        default=-1,
        )
    usd_path: bpy.props.StringProperty(
        subtype='FILE_PATH',
        name="USD Stage",
        default=""
        )
    is_live_mode: bpy.props.BoolProperty(
        name="Is Live Mode",
        default=False
        )
    is_live_update: bpy.props.BoolProperty(
        name="Is Live Update",
        default=False
        )
    is_depsgraph_update: bpy.props.BoolProperty(
        name="Is Depsgraph Update",
        description="",
        default=True
        )

    def get_info(self):
        return LiveModeInfo(self.liveUrl, self.storageUrl, self.channelId, self.get_user_id())

    def get_resolver_path(self):
        path = self.usd_path
        if not RenderStudioResolver.IsRenderStudioPath(path):
            if RenderStudioResolver.IsUnresovableToRenderStudioPath(path):
                path = RenderStudioResolver.Unresolve(path)
            else:
                return False
        log.debug("Resolved Path: ", path)
        return path

    def start_live_mode(self):
        if self.is_live_mode:
            return

        stage = self.get_stage()
        if not stage:
            stage = self.open_stage()

        if stage:
            info = self.get_info()
            RenderStudioResolver.StartLiveMode(info)
            self.is_live_mode = True
            log.debug("Start Live Mode: ", info.liveUrl, info.storageUrl, info.channelId, info.userId)

        else:
            log.debug("Failed Start Live Mode: ")

    def stop_live_mode(self):
        if self.is_live_mode:
            RenderStudioResolver.StopLiveMode()
            self.is_live_mode = False
            self.is_live_update = False

        log.debug("Stop Live Mode")

    def process_live_updates(self):
        log.debug(self.is_live_mode, self.is_live_update)
        if self.is_live_mode and not self.is_live_update:
            log.debug("Process Start Live Updates")
            self.is_live_update = True
            thread = Thread(target=self._sync, daemon=True)
            thread.start()

        else:
            log.debug("Process Stop Live Updates")
            self.is_live_update = False

    def _sync(self):
        while (self.is_live_update and self.is_live_mode):
            if RenderStudioResolver.ProcessLiveUpdates():
                self.is_depsgraph_update = False
                stage = self.get_stage()
                for prim in stage.GetPseudoRoot().GetAllChildren():
                    xform = UsdGeom.Xform(prim)
                    transform = get_xform_transform(xform)
                    obj = bpy.context.collection.objects.get(prim.GetName())
                    if obj:
                        obj.matrix_local = transform
                        log.debug("Updated: ", obj)

            self.is_depsgraph_update = True

    def get_user_id(self):
        return f"{self.userId}_{uuid.uuid4()}"

    def get_stage(self):
        stage = stage_cache.Find(Usd.StageCache.Id.FromLongInt(self.stageId))
        log.debug("Stage: ", stage)
        return stage

    def add_prim(self):
        stage = self.get_stage()
        prim, sphere = self.prim_name.split('/')
        UsdGeom.Xform.Define(stage, f'/{prim}')
        UsdGeom.Sphere.Define(stage, f'/{prim}/{sphere}')

    def import_stage(self, filepath=None):
        self.is_depsgraph_update = False
        filepath = self.usd_path if filepath is None else filepath
        bpy.ops.wm.usd_import(filepath=filepath)
        self.is_depsgraph_update = True
        log.debug("Import stage: ", filepath)

    def open_stage(self):
        path = self.get_resolver_path()
        if not path:
            log.warn("Failed USD Path")
            return False

        stage = Usd.Stage.Open(path)
        self.stageId = stage_cache.Insert(stage).ToLongInt()
        self.link_objects_to_usd()

        log.debug("Open stage: ", self.usd_path, path, stage)
        return stage

    def link_objects_to_usd(self):
        stage = self.get_stage()
        objects = bpy.context.collection.objects
        self.is_depsgraph_update = False
        for prim in stage.GetPseudoRoot().GetAllChildren():
            name = prim.GetName()
            obj = objects.get(name)
            if obj:
                obj.resolver.sdf_path = str(prim.GetPrimPath())
                log.debug("Link: ", obj, "<->", prim)

        self.is_depsgraph_update = True


def get_xform_transform(xform):
    transform = mathutils.Matrix(xform.GetLocalTransformation())
    return transform.transposed()

register_classes, unregister_classes = bpy.utils.register_classes_factory([
    RESOLVER_object_properties,
    RESOLVER_collection_properties,
    ])


def register():
    register_classes()


def unregister():
    unregister_classes()
