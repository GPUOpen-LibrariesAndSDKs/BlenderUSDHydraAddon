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
import bpy
from pxr import UsdGeom, Gf
from . import logging


log = logging.Log("updates")


def get_transform_local(obj: bpy.types.Object):
    return obj.matrix_local.transposed()


def on_depsgraph_update_post(scene, depsgraph):
    resolver = bpy.context.collection.resolver
    if not resolver.is_depsgraph_update:
        return
    for update in depsgraph.updates:
        if isinstance(update.id, bpy.types.Object):
            obj = update.id
            stage = bpy.context.collection.resolver.get_stage()
            if not obj.resolver.sdf_path:
                return

            prim = stage.GetPrimAtPath(obj.resolver.sdf_path)
            if not prim:
                return

            xform = UsdGeom.XformCommonAPI(prim)
            if update.is_updated_transform:
                xform.SetTranslate(Gf.Vec3d(tuple(obj.location)))
                xform.SetRotate(Gf.Vec3f(tuple(obj.rotation_euler)))
                xform.SetScale(Gf.Vec3f(tuple(obj.scale)))
                log.debug("Updated: ", prim, update.id)

            else:
                log.debug("Unsupported updates: ", prim, update.id)
