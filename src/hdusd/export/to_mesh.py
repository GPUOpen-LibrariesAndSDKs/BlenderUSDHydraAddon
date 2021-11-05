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
"""
This module exports following blender object types: 'CURVE', 'FONT', 'SURFACE', 'META'.
It converts such blender object into blender mesh and exports it as mesh.
"""

import bpy

from . import mesh

from ..utils import logging
log = logging.Log('export.to_mesh')


def sync(obj_prim, obj: bpy.types.Object, **kwargs):
    """ Converts object into blender's mesh and exports it as mesh """

    try:
        # This operation adds new mesh into bpy.data.meshes, that's why it should be removed after usage.
        # obj.to_mesh() could also return None for META objects.
        new_mesh = obj.to_mesh()
        log("sync", obj, new_mesh)

        if new_mesh:
            mesh.sync(obj_prim, obj, new_mesh, **kwargs)
            return True

        return False

    finally:
        # it's important to clear created mesh
        obj.to_mesh_clear()


def sync_update(obj_prim, obj: bpy.types.Object, **kwargs):
    """ Updates existing rpr mesh or creates a new mesh """

    log("sync_update", obj)

    stage = obj_prim.GetStage()
    for child_prim in obj_prim.GetAllChildren():
        stage.RemovePrim(child_prim.GetPath())

    sync(obj_prim, obj, **kwargs)
