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
import numpy as np
from pathlib import Path

import bpy
import mathutils

from pxr import Gf, Sdf, UsdGeom, UsdLux, Tf

from ...utils.image import cache_image_file
from ...utils import BLENDER_DATA_DIR

from ...utils import logging
log = logging.Log(tag='export.world')


@dataclass(init=False, eq=True, repr=True)
class WorldData:
    """ Comparable dataclass which holds all environment settings """

    color: tuple = (0, 0, 0)
    image: str = None
    intensity: float = 1.0
    rotation: tuple = (0, 0, 0)

    @staticmethod
    def init_from_world(world: bpy.types.World):
        """ Returns WorldData from bpy.types.World """
        data = WorldData()

        if not world.use_nodes:
            data.color = tuple(world.color)
            return data

        output_node = next((node for node in world.node_tree.nodes
                           if node.bl_idname == 'ShaderNodeOutputWorld' and node.is_active_output),
                           None)
        if not output_node:
            return data

        from .nodes import ShaderNodeOutputWorld

        node_parser = ShaderNodeOutputWorld(world, output_node)
        node_item = node_parser.export()
        if not node_item:
            return data

        d = node_item.data
        print(d)

        if isinstance(d, float):
            data.color = (d, d, d)
        if isinstance(d, tuple):
            data.color = d[:3]
        else:   # dict
            intensity = d.get('intensity', 1.0)
            if isinstance(intensity, tuple):
                intensity = intensity[0]

            data.intensity = intensity

            color = d.get('color')
            if color:
                if isinstance(color, float):
                    data.color = (color, color, color)
                if isinstance(color, tuple):
                    data.color = color[:3]
                else:   # dict
                    image = color.get('image')
                    if image:
                        data.image = cache_image_file(image)
            else:
                image = d.get('image')
                if image:
                    data.image = cache_image_file(image)

        return data

    @staticmethod
    def init_from_shading(shading):
        data = WorldData()
        data.intensity = shading.studio_light_intensity
        data.rotation = (0.0, 0.0, shading.studio_light_rotate_z)
        data.image = str(BLENDER_DATA_DIR / "studiolights/world" / shading.studio_light)
        return data


def sync(root_prim, world: bpy.types.World, **kwargs):

    # get the World IBL image
    data = WorldData.init_from_world(world)
    print(data)

    #
    #
    #
    # stage = root_prim.GetStage()
    #
    # if not data.cycles_ibl.image:
    #     # TODO create image from environment color data if no image used
    #     return
    #
    # # create Dome light
    # xform = UsdGeom.Xform.Define(stage, root_prim.GetPath().AppendChild("_world"))
    # obj_prim = xform.GetPrim()
    #
    # usd_light = UsdLux.DomeLight.Define(stage, obj_prim.GetPath().AppendChild(Tf.MakeValidIdentifier(world.name)))
    # usd_light.ClearXformOpOrder()
    # usd_light.OrientToStageUpAxis()
    #
    # p = Sdf.AssetPath(data.cycles_ibl.image)
    # usd_light.CreateTextureFileAttr(p)
    #
    # # set correct Dome light rotation
    # matrix = np.identity(4)
    # rotation = data.cycles_ibl.rotation
    # euler = mathutils.Euler((-rotation[0], -rotation[1] + np.pi, -rotation[2] - np.pi / 2))
    #
    # rotation_matrix = np.array(euler.to_matrix(), dtype=np.float32)
    #
    # matrix[:3, :3] = rotation_matrix[:, :]
    #
    # xform.ClearXformOpOrder()
    # xform.AddTransformOp().Set(Gf.Matrix4d(matrix))
