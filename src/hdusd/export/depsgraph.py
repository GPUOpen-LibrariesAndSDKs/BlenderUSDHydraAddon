#**********************************************************************
# Copyright 2020 Advanced Micro Devices, Inc
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
#********************************************************************
from pxr import Usd, UsdGeom

import bpy

from . import object, world, sdf_path
from .. import utils

from ..utils import logging
log = logging.Log(tag='export.depsgraph')


ITERATED_OBJECT_TYPES = ('MESH', 'LIGHT', 'CURVE', 'FONT', 'SURFACE', 'META', 'VOLUME', 'CAMERA')


def depsgraph_objects(depsgraph, space_data, use_scene_lights):
    for obj in depsgraph.objects:
        if obj.type not in ITERATED_OBJECT_TYPES:
            continue

        if obj.type == 'LIGHT' and not use_scene_lights:
            continue

        if space_data and not obj.visible_in_viewport_get(space_data):
            continue

        yield obj


def _usd_path(depsgraph, engine):
    return utils.usd_temp_path(depsgraph, engine)


def sync(depsgraph: bpy.types.Depsgraph, **kwargs):
    log("sync", depsgraph)

    sync_callback = kwargs.get('sync_callback')
    test_break = kwargs.get('test_break')
    space_data = kwargs.get('space_data')
    use_scene_lights = kwargs.get('use_scene_lights', True)
    engine = kwargs['engine']

    stage = Usd.Stage.CreateNew(str(_usd_path(depsgraph, engine)))
    UsdGeom.SetStageMetersPerUnit(stage, 1)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)

    root_prim = stage.DefinePrim(f"/{sdf_path(depsgraph.scene.name)}", 'Xform')
    stage.SetDefaultPrim(root_prim)

    objects_prim = stage.DefinePrim(f"{root_prim.GetPath()}/objects", 'Xform')

    objects_len = len(depsgraph.objects)
    for i, obj in enumerate(depsgraph_objects(depsgraph, space_data, use_scene_lights)):
        if test_break and test_break():
            return None

        if sync_callback:
            sync_callback(f"Syncing object {i}/{objects_len}: {obj.name}")

        try:
            object.sync(objects_prim, obj, **kwargs)
        except Exception as e:
            log.error(e)

    world.sync(root_prim, depsgraph.scene.world)

    return stage


def get_stage(depsgraph, engine):
    path = _usd_path(depsgraph, engine)
    if not path.is_file():
        return None

    return Usd.Stage.Open(str(path))
