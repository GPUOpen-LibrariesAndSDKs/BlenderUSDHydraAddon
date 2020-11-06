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
from dataclasses import dataclass, field
from typing import Tuple

import numpy as np
import math
from pathlib import Path

import bpy
import mathutils

from pxr import UsdLux

from . import image, sdf_path
from .image import ImagePixels

from ..utils import logging
log = logging.Log(tag='export.world')


WARNING_IMAGE_NOT_DEFINED_COLOR = (1.0, 0.0, 1.0)
STUDIO_LIGHT_DEFAULT_COLOR = (0.051, 0.051, 0.051)  # Blender's default background color in viewport


def set_light_rotation(rpr_light, rotation: Tuple[float]) -> np.array:
    """ Calculates rotation matrix from gizmo rotation """

    matrix = np.identity(4, dtype=np.float32)
    euler = mathutils.Euler((rotation[0], rotation[1], rotation[2] - np.pi / 2))

    rotation_matrix = np.array(euler.to_matrix(), dtype=np.float32)
    fixup = np.array([[1, 0, 0],
                      [0, 0, 1],
                      [0, 1, 0]], dtype=np.float32)

    matrix[:3, :3] = np.dot(fixup, rotation_matrix)
    rpr_light.set_transform(matrix, False)
    return matrix


def sync(obj_prim, world: bpy.types.World, **kwargs):
    if not world.use_nodes:
        return

    color = world.color
    ibl_path = ""
    if world.use_nodes:
        output = world.node_tree.get_output_node('ALL')
        if not output:
            output = world.node_tree.get_output_node('CYCLES')

        if not output or not output.inputs['Surface'].is_linked:
            return

        linked_node = output.inputs['Surface'].links[0].from_node
        if linked_node.type != 'BACKGROUND':
            return

        color = linked_node.inputs['Color'].default_value
        if linked_node.inputs['Color'].is_linked:
            color_node = linked_node.inputs['Color'].links[0].from_node
            if color_node.type != 'TEX_ENVIRONMENT':
                return
            if not color_node.image or not color_node.image.filepath:
                return
            img_path = color_node.image.filepath_from_user()
            if not Path(img_path).is_file():
                return

            ibl_path = str(img_path)

    stage = obj_prim.GetStage()

    try:
        usd_light = UsdLux.DomeLight.Define(
            stage, f"{obj_prim.GetPath()}/{sdf_path(world.name)}")

        if ibl_path:
            from pxr import Sdf
            p = Sdf.AssetPath(ibl_path)
            usd_light.CreateTextureFileAttr(p)
    except Exception as e:
        log.warn(f"World export error: {str(e)}")

    # data = WorldData.init_from_world(world)
    # data.export(rpr_context)
