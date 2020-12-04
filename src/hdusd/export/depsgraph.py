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


def depsgraph_objects(depsgraph, space_data=None, use_scene_lights=True):
    for obj in depsgraph.objects:
        if obj.type not in ITERATED_OBJECT_TYPES:
            continue

        if obj.type == 'LIGHT' and not use_scene_lights:
            continue

        if space_data and not obj.visible_in_viewport_get(space_data):
            continue

        yield obj


def sync(stage, depsgraph: bpy.types.Depsgraph, **kwargs):
    log("sync", depsgraph)

    sync_callback = kwargs.get('sync_callback')
    test_break = kwargs.get('test_break')
    space_data = kwargs.get('space_data')
    use_scene_lights = kwargs.get('use_scene_lights', True)

    UsdGeom.SetStageMetersPerUnit(stage, 1)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)

    root_prim = stage.DefinePrim(f"/{sdf_path(depsgraph.scene.name)}")
    stage.SetDefaultPrim(root_prim)

    objects_prim = stage.DefinePrim(f"{root_prim.GetPath()}/objects")

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

    world.sync(root_prim, depsgraph.scene.world, **kwargs)


def sync_update(stage, depsgraph, **kwargs):
    scene = depsgraph.scene

    root_prim = stage.GetPrimAtPath(f"/{sdf_path(scene.name)}")
    objects_prim = root_prim.GetChild("objects")

    # get supported updates and sort by priorities
    updates = []
    for obj_type in (bpy.types.Material, bpy.types.Object, bpy.types.Collection):
        updates.extend(update for update in depsgraph.updates if isinstance(update.id, obj_type))

    sync_collection = False
    for update in updates:
        obj = update.id
        log("sync_update", obj)

        if isinstance(obj, bpy.types.Object) and not obj.hdusd.is_usd:
            object.sync_update(objects_prim, obj,
                               update.is_updated_geometry,
                               update.is_updated_transform)
            continue

        if isinstance(obj, bpy.types.Collection):
            sync_collection = True
            continue

    if sync_collection:
        space_data = kwargs.get('space_data')
        use_scene_lights = kwargs.get('use_scene_lights', True)

        depsgraph_keys = set(object.sdf_name(obj)
                             for obj in depsgraph_objects(depsgraph, space_data, use_scene_lights))
        usd_object_keys = set(prim.GetName() for prim in objects_prim.GetAllChildren())
        keys_to_remove = usd_object_keys - depsgraph_keys
        keys_to_add = depsgraph_keys - usd_object_keys

        if keys_to_remove:
            log("Object keys to remove", keys_to_remove)
            for key in keys_to_remove:
                stage.RemovePrim(f"{objects_prim.GetPath()}/{key}")

        if keys_to_add:
            log("Object keys to add", keys_to_add)
            for obj in depsgraph_objects(depsgraph, space_data, use_scene_lights):
                obj_key = object.sdf_name(obj)
                if obj_key not in keys_to_add:
                    continue

                object.sync(objects_prim, obj)
