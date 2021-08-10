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
from dataclasses import dataclass

from pxr import UsdGeom, Gf, Tf
import bpy
import mathutils

from . import mesh, camera, to_mesh, light

from ..utils import logging
log = logging.Log(tag='export.instance')


SUPPORTED_TYPES = ('MESH', 'LIGHT', 'CURVE', 'FONT', 'SURFACE', 'META', 'CAMERA')


@dataclass(init=False)
class ObjectData:
    object: bpy.types.Object
    instance_id: int
    transform: mathutils.Matrix

    def __init__(self, instance):
        self.object = instance.object
        self.instance_id = abs(instance.random_id)
        self.transform = instance.matrix_world.transposed()

    @property
    def sdf_name(self):
        name = Tf.MakeValidIdentifier(self.object.name_full)
        return name if self.instance_id == 0 else f"{name}_{self.instance_id}"

    @staticmethod
    def depsgraph_objects(depsgraph, *, space_data=None, use_scene_lights=True):
        for instance in depsgraph.object_instances:
            obj = instance.object
            if obj.type not in SUPPORTED_TYPES:
                continue

            if obj.type == 'LIGHT' and not use_scene_lights:
                continue

            if space_data and not instance.is_instance and not obj.visible_in_viewport_get(space_data):
                continue

            yield ObjectData(instance)


def sdf_name(obj: bpy.types.Object):
    return Tf.MakeValidIdentifier(obj.name_full)


def get_transform(obj: bpy.types.Object):
    return obj.matrix_world.transposed()


def get_transform_local(obj: bpy.types.Object):
    return obj.matrix_local.transposed()


def sync(objects_prim, obj_data: ObjectData, **kwargs):
    """ sync the object and any data attached """
    log("sync", obj_data.object, obj_data.instance_id)

    stage = objects_prim.GetStage()
    xform = UsdGeom.Xform.Define(stage, objects_prim.GetPath().AppendChild(obj_data.sdf_name))
    obj_prim = xform.GetPrim()

    # setting transform
    xform.MakeMatrixXform().Set(Gf.Matrix4d(obj_data.transform))

    obj = obj_data.object
    if obj.type == 'MESH':
        if obj.mode == 'OBJECT':
            # if in edit mode use to_mesh
            mesh.sync(obj_prim, obj, **kwargs)
        else:
            to_mesh.sync(obj_prim, obj, **kwargs)

    elif obj.type == 'LIGHT':
        light.sync(obj_prim, obj, **kwargs)

    elif obj.type == 'CAMERA':
        camera.sync(obj_prim, obj, **kwargs)

    else:
        to_mesh.sync(obj_prim, obj, **kwargs)


def sync_update(root_prim, obj: bpy.types.Object, is_updated_geometry, is_updated_transform,
                **kwargs):
    """ Updates existing rpr object. Checks obj.type and calls corresponded sync_update() """

    log("sync_update", obj, is_updated_geometry, is_updated_transform)

    obj_prim = root_prim.GetChild(sdf_name(obj))
    if not obj_prim.IsValid():
        sync(root_prim, obj, **kwargs)
        return

    if is_updated_transform:
        xform = UsdGeom.Xform(obj_prim)
        xform.MakeMatrixXform().Set(Gf.Matrix4d(get_transform(obj)))

    if is_updated_geometry:
        if obj.type == 'MESH':
            if obj.mode == 'OBJECT':
                mesh.sync_update(obj_prim, obj, **kwargs)
            else:
                to_mesh.sync_update(obj_prim, obj, **kwargs)

        elif obj.type == 'LIGHT':
            light.sync_update(obj_prim, obj, **kwargs)

        elif obj.type == 'CAMERA':
            camera.sync_update(obj_prim, obj, **kwargs)

        elif obj.type in ('CURVE', 'FONT', 'SURFACE', 'META'):
            to_mesh.sync_update(obj_prim, obj, **kwargs)

        elif obj.type == 'EMPTY':
            pass

        else:
            log.warn("Not supported object to sync_update", obj, obj.type)
