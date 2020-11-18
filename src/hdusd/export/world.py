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

from pxr import Gf, Sdf, UsdGeom, UsdLux

from . import image, sdf_path

from ..utils import logging
log = logging.Log(tag='export.world')


WARNING_IMAGE_NOT_DEFINED_COLOR = (1.0, 0.0, 1.0)
STUDIO_LIGHT_DEFAULT_COLOR = (0.051, 0.051, 0.051)  # Blender's default background color in viewport


@dataclass(init=False, eq=True, repr=True)
class WorldData:
    """ Comparable dataclass which holds all environment settings """

    @dataclass(eq=True)
    class IblData:
        color: tuple = (0, 0, 0)
        image: str = None
        studio_light: str = None
        rotation: tuple = (0, 0, 0)

        @staticmethod
        def init_from_cycles(world: bpy.types.World):
            data = WorldData.IblData()

            data.color = world.color[:3]

            if not world.use_nodes:
                return data

            # Parse the simplest environment IBL image nodes config:
            # Mapping -> Environment Image -> Background -> World Output
            output = world.node_tree.get_output_node('ALL')
            if not output:
                output = world.node_tree.get_output_node('CYCLES')

            if not output or not output.inputs['Surface'].is_linked:
                return data

            # Background node
            background_node = output.inputs['Surface'].links[0].from_node
            if background_node.type != 'BACKGROUND':
                return data

            data.color = background_node.inputs['Color'].default_value[:3]

            # Environment Image node => image file info
            if not background_node.inputs['Color'].is_linked:
                return data
            environment_node = background_node.inputs['Color'].links[0].from_node
            if environment_node.type != 'TEX_ENVIRONMENT':
                return data
            if not environment_node.image or not environment_node.image.filepath:
                return data
            img_path = environment_node.image.filepath_from_user()

            # TODO extract studio lights and packed images
            if not Path(img_path).is_file():
                return data
            data.image = str(img_path)

            # Mapping node => rotation info
            if not environment_node.inputs['Vector'].is_linked:
                return data
            mapping_node = environment_node.inputs['Vector'].links[0].from_node
            if mapping_node.type != 'MAPPING':
                return data
            data.rotation = tuple(mapping_node.inputs[2].default_value)

            return data

        @staticmethod
        def init_from_shading(shading):
            data = WorldData.IblData()
            data.studio_light = shading.studio_light
            return data

    cycles_ibl: IblData = None
    # TODO support studio light settings
    # TODO support RPR Environment settings as an option

    @staticmethod
    def init_from_world(world: bpy.types.World):
        """ Returns WorldData from bpy.types.World """
        data = WorldData()

        data.cycles_ibl = WorldData.IblData.init_from_cycles(world)

        return data


def sync(root_prim, world: bpy.types.World, **kwargs):
    is_gl_mode = kwargs.get('is_gl_delegate', False)

    if is_gl_mode:
        # TODO export correct Dome light with texture for GL mode
        return

    # get the World IBL image
    data = WorldData.init_from_world(world)
    log.info(f"world data: {data}")

    stage = root_prim.GetStage()

    if not data.cycles_ibl.image:
        # TODO create image from environment color data if no image used
        return

    # create Dome light
    xform = UsdGeom.Xform.Define(stage, f"{root_prim.GetPath()}/_world")
    obj_prim = xform.GetPrim()

    usd_light = UsdLux.DomeLight.Define(
        stage, f"{obj_prim.GetPath()}/_world/{sdf_path(world.name)}")
    usd_light.ClearXformOpOrder()
    usd_light.OrientToStageUpAxis()

    p = Sdf.AssetPath(data.cycles_ibl.image)
    usd_light.CreateTextureFileAttr(p)

    # set correct Dome light rotation
    matrix = np.identity(4)
    rotation = data.cycles_ibl.rotation
    euler = mathutils.Euler((-rotation[0], -rotation[1] + np.pi, -rotation[2] - np.pi / 2))

    rotation_matrix = np.array(euler.to_matrix(), dtype=np.float32)

    matrix[:3, :3] = rotation_matrix[:, :]

    xform.ClearXformOpOrder()
    xform.AddTransformOp().Set(Gf.Matrix4d(matrix))
