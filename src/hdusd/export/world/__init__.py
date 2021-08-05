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

    color: tuple = (0.0, 0.0, 0.0)
    image: str = None
    intensity: float = 1.0
    rotation: tuple = (0.0, 0.0, 0.0)

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

        if isinstance(d, float):
            data.color = (d, d, d)
            return data

        if isinstance(d, tuple):
            data.color = d[:3]
            return data

        # d is dict here

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

        rotation = d.get('rotation')
        if isinstance(rotation, tuple):
            data.rotation = rotation[:3]

        return data

    @staticmethod
    def init_from_shading(shading):
        data = WorldData()
        data.intensity = shading.studio_light_intensity
        data.rotation = (0.0, 0.0, shading.studio_light_rotate_z)
        data.image = BLENDER_DATA_DIR / "studiolights/world" / shading.studio_light
        return data


def sync(root_prim, world: bpy.types.World):
    data = WorldData.init_from_world(world)

    stage = root_prim.GetStage()

    obj_prim = stage.DefinePrim(root_prim.GetPath().AppendChild("World"))
    usd_light = UsdLux.DomeLight.Define(stage,
        obj_prim.GetPath().AppendChild(Tf.MakeValidIdentifier(world.name)))
    usd_light.OrientToStageUpAxis()

    if data.image:
        usd_light.CreateTextureFileAttr(str(data.image))
    else:
        usd_light.CreateColorAttr(data.color)

    usd_light.CreateIntensityAttr(data.intensity)

    # # set correct Dome light rotation
    usd_light.AddRotateXOp().Set(180.0)
    usd_light.AddRotateYOp().Set(-90.0)
    # TODO: enable rotation angles


def sync_update(root_prim, world: bpy.types.World):
    stage = root_prim.GetStage()

    usd_light = UsdLux.DomeLight.Define(stage,
        Sdf.Path('/World').AppendChild(Tf.MakeValidIdentifier(world.name)))

    # removing prev settings
    usd_light.CreateColorAttr().Clear()
    usd_light.CreateTextureFileAttr().Clear()
    usd_light.ClearXformOpOrder()

    sync(root_prim, world)
