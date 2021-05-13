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
from pxr import UsdGeom, Gf
import bpy

from . import mesh, camera, to_mesh, light, sdf_path

from ..utils import logging
log = logging.Log(tag='export.object')


def sdf_name(obj: bpy.types.Object):
    return sdf_path(obj.name_full)


def get_transform(obj: bpy.types.Object):
    return obj.matrix_world.transposed()


def sync(objects_prim, obj: bpy.types.Object, **kwargs):
    """ sync the object and any data attached """
    log("sync", obj, obj.type)

    stage = objects_prim.GetStage()
    xform = UsdGeom.Xform.Define(stage, objects_prim.GetPath().AppendChild(sdf_name(obj)))
    obj_prim = xform.GetPrim()

    # setting transform
    xform.MakeMatrixXform().Set(Gf.Matrix4d(get_transform(obj)))

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

    elif obj.type in ('CURVE', 'FONT', 'SURFACE', 'META'):
        to_mesh.sync(obj_prim, obj, **kwargs)

    elif obj.type == 'EMPTY':
        pass

    else:
        stage.RemovePrim(obj_prim.GetPath())
        log.warn("Object to sync not supported", obj, obj.type)


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

        elif obj.type in ('CURVE', 'FONT', 'SURFACE', 'META'):
            to_mesh.sync_update(obj_prim, obj, **kwargs)

        elif obj.type == 'EMPTY':
            pass

        else:
            log.warn("Unsupported object to sync_update", obj, obj.type)


def sync_update_material(root_prim, obj: bpy.types.Object, **kwargs):
    log("sync_update_material", obj)

    obj_prim = root_prim.GetChild(sdf_name(obj))
    if not obj_prim.IsValid():
        sync(root_prim, obj, **kwargs)
        return

    if obj.type in ('MESH', 'CURVE', 'FONT', 'SURFACE', 'META'):
        mesh.sync_update_material(obj_prim, obj)

    else:
        log.warn("Unsupported object to sync_update_material", obj, obj.type)
