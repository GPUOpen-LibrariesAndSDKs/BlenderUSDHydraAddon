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


def get_material_output_node(material):
    """ Finds output node in material tree and exports it """
    if not material.node_tree:
        # there could be a situation when node_tree is None
        return None

    return next((node for node in material.node_tree.nodes
                 if node.bl_idname == 'ShaderNodeOutputMaterial' and node.is_active_output),
                None)


def get_material_input_node(mat):
    """ Find the material node attached to output node 'input_socket_key' input """
    output_node = get_material_output_node(mat)
    if not output_node:
        return None

    socket_in = output_node.inputs['Surface']
    if not socket_in.is_linked or not socket_in.links[0].is_valid:
        return None

    return socket_in.links[0].from_node


def sync(materials_prim, mat: bpy.types.Material, obj: bpy.types.Object):
    """
    If material exists: returns existing material unless force_update is used
    In other cases: returns None
    """

    log("sync", mat, obj)

    if mat.hdusd.mx_node_tree:
        return sync_mx(materials_prim, mat.hdusd.mx_node_tree, obj)

    output_node = get_material_output_node(mat)
    if not output_node:
        log("No output node", mat)
        return None

    node = get_material_input_node(mat)
    if not node:
        return None

    stage = materials_prim.GetStage()
    mat_path = f"{materials_prim.GetPath()}/{sdf_name(mat)}"
    usd_mat = UsdShade.Material.Define(stage, mat_path)

    # create appropriate USD shader
    if node.bl_idname == 'ShaderNodeBsdfPrincipled':
        create_principled_shader(usd_mat, node)
    elif node.bl_idname == 'ShaderNodeEmission':
        create_emission_shader(usd_mat, node)
    elif node.bl_idname == 'ShaderNodeBsdfDiffuse':  # used by Material Preview
        create_diffuse_shader(usd_mat, node)
    else:
        log.warn("Unsupported node", node, mat)

    return usd_mat


def get_input_default(node, socket_key):
    val = node.inputs[socket_key].default_value
    if isinstance(val, (int, float)):
        return float(val)

    if len(val) in (3, 4):
        return tuple(val[:3])

    if isinstance(val, str):
        return val

    raise TypeError("Unknown value type", val)


def create_principled_shader(usd_mat, node):
    stage = usd_mat.GetPrim().GetStage()
    shader_key = f"{usd_mat.GetPath()}/PBRShader"

    pbr_shader = UsdShade.Shader.Define(stage, shader_key)
    pbr_shader.CreateIdAttr("UsdPreviewSurface")
    pbr_shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Float3).Set(get_input_default(node, 'Base Color',))
    pbr_shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(get_input_default(node, 'Roughness'))
    pbr_shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(get_input_default(node, 'Metallic'))
    pbr_shader.CreateInput("clearcoat", Sdf.ValueTypeNames.Float).Set(get_input_default(node, 'Clearcoat'))
    pbr_shader.CreateInput("clearcoatRoughness", Sdf.ValueTypeNames.Float).Set(get_input_default(node, 'Clearcoat Roughness'))
    pbr_shader.CreateInput("emissiveColor", Sdf.ValueTypeNames.Float3).Set(get_input_default(node, 'Emission'))
    pbr_shader.CreateInput("ior", Sdf.ValueTypeNames.Float).Set(get_input_default(node, 'IOR'))
    pbr_shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(1.0 - get_input_default(node, 'Transmission'))

    usd_mat.CreateSurfaceOutput().ConnectToSource(pbr_shader, "surface")


def create_diffuse_shader(usd_mat, node):
    stage = usd_mat.GetPrim().GetStage()
    shader_key = f"{usd_mat.GetPath()}/DiffuseShader"

    pbr_shader = UsdShade.Shader.Define(stage, shader_key)
    pbr_shader.CreateIdAttr("UsdPreviewSurface")
    pbr_shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Float3).Set(get_input_default(node, 'Color',))
    pbr_shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(get_input_default(node, 'Roughness'))

    usd_mat.CreateSurfaceOutput().ConnectToSource(pbr_shader, "surface")


def create_emission_shader(usd_mat, node):
    stage = usd_mat.GetPrim().GetStage()
    shader_key = f"{usd_mat.GetPath()}/PBREmissionShader"

    pbr_shader = UsdShade.Shader.Define(stage, shader_key)
    pbr_shader.CreateIdAttr("UsdPreviewSurface")
    emission_color = get_input_default(node, 'Color')
    strength = get_input_default(node, 'Strength')
    emission_color = tuple(e * strength for e in emission_color)

    pbr_shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Float3).Set(emission_color)
    pbr_shader.CreateInput("emissiveColor", Sdf.ValueTypeNames.Float3).Set(emission_color)

    usd_mat.CreateSurfaceOutput().ConnectToSource(pbr_shader, "surface")


def sync_update(materials_prim, mat: bpy.types.Material, obj: bpy.types.Object):
    """ Recreates existing material """

    log("sync_update", mat)

    stage = materials_prim.GetStage()
    mat_path = f"{materials_prim.GetPath()}/{sdf_name(mat)}"
    usd_mat = stage.GetPrimAtPath(mat_path)
    if usd_mat.IsValid():
        stage.RemovePrim(mat_path)

    sync(materials_prim, mat, obj)


def sync_mx(materials_prim, mx_node_tree, obj):
    log("sync_mx", mx_node_tree, obj)

    doc = mx_node_tree.export()
    if not doc:
        log.warn("No output node", mx_node_tree)
        return None

    mx_file = utils.get_temp_file(".mtlx")
    mx.writeToXmlFile(doc, str(mx_file))
    surfacematerial = next(node for node in doc.getNodes()
                           if node.getNamePath() == 'surfacematerial')

    stage = materials_prim.GetStage()
    mat_path = f"{materials_prim.GetPath()}/{sdf_name(mx_node_tree)}"
    usd_mat = UsdShade.Material.Define(stage, mat_path)
    shader = UsdShade.Shader.Define(stage, f"{usd_mat.GetPath()}/rpr_materialx_node")
    shader.CreateIdAttr("rpr_materialx_node")

    shader.CreateInput("file", Sdf.ValueTypeNames.Asset).Set(f"./{mx_file.name}")
    shader.CreateInput("surfaceElement", Sdf.ValueTypeNames.String).Set(surfacematerial.getName())

    out = usd_mat.CreateSurfaceOutput("rpr")
    out.ConnectToSource(shader, "surface")
    # shader.CreateInput("stPrimvarName", Sdf.ValueTypeNames.String).Set("UVMap")

    return usd_mat
