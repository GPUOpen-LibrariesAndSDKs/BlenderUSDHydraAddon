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
import bpy

from pxr import Sdf, UsdShade
import MaterialX as mx

from . import sdf_path
from .. import utils
from ..utils import logging
log = logging.Log(tag='export.material')


def sdf_name(mat: bpy.types.Material, input_socket_key='Surface'):
    ret = sdf_path(mat.name_full)
    if input_socket_key != 'Surface':
        ret += "/" + sdf_path(mat.name_full)

    return ret


def sync(materials_prim, mat: bpy.types.Material, obj: bpy.types.Object):
    """
    If material exists: returns existing material unless force_update is used
    In other cases: returns None
    """

    log("sync", mat, obj)

    doc = mat.hdusd.export(obj)
    if not doc:
        log.warn("MX export failed", mat)
        return None

    mx_file = utils.get_temp_file(".mtlx")
    mx.writeToXmlFile(doc, str(mx_file))
    surfacematerial = next(node for node in doc.getNodes()
                           if node.getCategory() == 'surfacematerial')

    stage = materials_prim.GetStage()
    mat_path = materials_prim.GetPath().AppendChild(sdf_name(mat))
    usd_mat = UsdShade.Material.Define(stage, mat_path)
    shader = UsdShade.Shader.Define(stage, usd_mat.GetPath().AppendChild("rpr_materialx_node"))
    shader.CreateIdAttr("rpr_materialx_node")

    shader.CreateInput("file", Sdf.ValueTypeNames.Asset).Set(f"./{mx_file.name}")
    shader.CreateInput("surfaceElement", Sdf.ValueTypeNames.String).Set(surfacematerial.getName())

    out_mat = usd_mat.CreateSurfaceOutput("rpr")
    out_shader = shader.CreateOutput('surface', Sdf.ValueTypeNames.Token)
    out_mat.ConnectToSource(out_shader)
    # shader.CreateInput("stPrimvarName", Sdf.ValueTypeNames.String).Set("UVMap")

    return usd_mat


def sync_update(materials_prim, mat: bpy.types.Material, obj: bpy.types.Object):
    """ Recreates existing material """

    log("sync_update", mat)

    stage = materials_prim.GetStage()
    mat_path = f"{materials_prim.GetPath()}/{sdf_name(mat)}"
    usd_mat = stage.GetPrimAtPath(mat_path)
    if usd_mat.IsValid():
        stage.RemovePrim(mat_path)

    sync(materials_prim, mat, obj)


def sync_update_all(root_prim, mat: bpy.types.Material):
    print(root_prim, mat)
