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

from pxr import UsdGeom, Gf, Tf, UsdShade
import bpy
import mathutils

from . import mesh, camera, to_mesh, light, material

from ..utils import logging
log = logging.Log(tag='export.object')


SUPPORTED_TYPES = ('MESH', 'LIGHT', 'CURVE', 'FONT', 'SURFACE', 'META', 'CAMERA', 'EMPTY')


@dataclass(init=False)
class ObjectData:
    object: bpy.types.Object
    instance_id: int
    transform: mathutils.Matrix
    parent: bpy.types.Object
    is_particle: bool

    @staticmethod
    def from_object(obj):
        data = ObjectData()
        data.object = obj
        data.instance_id = 0
        data.transform = obj.matrix_world.transposed()
        data.parent = obj.parent
        data.is_particle = False
        return data

    @staticmethod
    def from_instance(instance):
        data = ObjectData()
        data.object = instance.object
        data.instance_id = abs(instance.random_id)
        data.transform = instance.matrix_world.transposed()
        data.parent = instance.parent
        data.is_particle = bool(instance.particle_system)
        return data

    @property
    def sdf_name(self):
        name = Tf.MakeValidIdentifier(self.object.name_full)
        return name if self.instance_id == 0 else f"{name}_{self.instance_id}"

    @staticmethod
    def depsgraph_objects(depsgraph, *, space_data=None,
                          use_scene_lights=True, use_scene_cameras=True):
        for instance in depsgraph.object_instances:
            obj = instance.object
            if obj.type not in SUPPORTED_TYPES or instance.object.hdusd.is_usd:
                continue

            if obj.type == 'LIGHT' and not use_scene_lights:
                continue

            if obj.type == 'CAMERA' and not use_scene_cameras:
                continue

            if space_data and not instance.is_instance and not obj.visible_in_viewport_get(space_data):
                continue

            yield ObjectData.from_instance(instance)


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

    if obj_data.is_particle:
        usd_mesh = UsdGeom.Mesh.Define(stage, obj_prim.GetPath().AppendChild(
            sdf_name(obj.original)))
        mesh_prim = stage.DefinePrim(f"/{sdf_name(obj.original)}"
                                         f"/{sdf_name(obj.data)}", 'Mesh')
        usd_mesh.GetPrim().GetReferences().AddInternalReference(mesh_prim.GetPath())

        if obj.active_material is not None:
            material_prim = stage.DefinePrim(
                f"/{sdf_name(obj.original)}"
                f"/{material.sdf_name(obj.active_material)}", 'Material')

            usd_material = UsdShade.Material.Get(stage, material_prim.GetPath())
            UsdShade.MaterialBindingAPI(usd_mesh).Bind(usd_material)

        return

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

    elif obj.type in ('EMPTY', 'ARMATURE'):
        pass

    else:
        to_mesh.sync(obj_prim, obj, **kwargs)


def sync_update(root_prim, obj_data: ObjectData, is_updated_geometry, is_updated_transform,
                **kwargs):
    """ Updates existing rpr object. Checks obj.type and calls corresponded sync_update() """

    log("sync_update", obj_data.object, obj_data.instance_id,
        is_updated_geometry, is_updated_transform)

    obj_prim = root_prim.GetChild(obj_data.sdf_name)
    if not obj_prim.IsValid():
        sync(root_prim, obj_data, **kwargs)
        return

    if is_updated_transform:
        xform = UsdGeom.Xform(obj_prim)
        xform.MakeMatrixXform().Set(Gf.Matrix4d(obj_data.transform))

    if is_updated_geometry:
        obj = obj_data.object
        if obj.type == 'MESH':
            if obj.mode == 'OBJECT':
                mesh.sync_update(obj_prim, obj, **kwargs)
            else:
                to_mesh.sync_update(obj_prim, obj, **kwargs)

        elif obj.type == 'LIGHT':
            light.sync_update(obj_prim, obj, **kwargs)

        elif obj.type == 'CAMERA':
            camera.sync_update(obj_prim, obj, **kwargs)

        elif obj.type in ('EMPTY', 'ARMATURE'):
            pass

        else:
            to_mesh.sync_update(obj_prim, obj, **kwargs)
