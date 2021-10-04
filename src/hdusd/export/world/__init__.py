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

import bpy

from pxr import Sdf, UsdLux, Tf

from ...utils.image import cache_image_file
from ...utils import BLENDER_DATA_DIR

from ...utils import logging
log = logging.Log(tag='export.world')


PRIM_NAME = "World"


@dataclass(init=False, eq=True, repr=True)
class WorldData:
    """ Comparable dataclass which holds all environment settings """

    color: tuple = (0.0, 0.0, 0.0)
    image: str = None
    intensity: float = 1.0
    rotation: tuple = (0.0, 0.0, 0.0)
    transparency: float = 1.0

    @property
    def clear_color(self):
        color = [c * self.intensity for c in self.color]
        color.append(self.transparency)
        return tuple(color)

    @staticmethod
    def init_from_world(world: bpy.types.World):
        """ Returns WorldData from bpy.types.World """
        data = WorldData()

        if not world:
            return data

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

        node_data = node_item.data

        if isinstance(node_data, float):
            data.color = (node_data, node_data, node_data)
            data.transparency = 1.0
            return data

        if isinstance(node_data, tuple):
            data.color = node_data[:3]
            data.transparency = node_data[3]
            return data

        # node_data is dict here

        intensity = node_data.get('intensity', 1.0)
        if isinstance(intensity, tuple):
            intensity = intensity[0]

        data.intensity = intensity

        color = node_data.get('color')
        if color is None:
            image = node_data.get('image')
            if image:
                data.image = cache_image_file(image)

        elif isinstance(color, float):
            data.color = (color, color, color)
            data.transparency = color

        elif isinstance(color, tuple):
            data.color = color[:3]
            data.transparency = color[3]

        else:   # dict
            image = color.get('image')
            if image:
                data.image = cache_image_file(image)

        rotation = node_data.get('rotation')
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

    @staticmethod
    def init_from_stage(stage):
        data = WorldData()

        light_prim = next((prim for prim in stage.TraverseAll() if
                           prim.GetTypeName() == 'DomeLight'), None)
        if light_prim:
            data.color = light_prim.GetAttribute('inputs:color').Get()
            data.intensity = light_prim.GetAttribute('inputs:intensity').Get()
            data.transparency = light_prim.GetAttribute('inputs:transparency').Get()

        return data


def sync(root_prim, world: bpy.types.World):
    data = WorldData.init_from_world(world)

    stage = root_prim.GetStage()

    obj_prim = stage.DefinePrim(root_prim.GetPath().AppendChild(PRIM_NAME))
    usd_light = UsdLux.DomeLight.Define(stage,
        obj_prim.GetPath().AppendChild(Tf.MakeValidIdentifier(world.name)))
    usd_light.OrientToStageUpAxis()

    if data.image:
        usd_light.CreateTextureFileAttr(str(data.image))
    else:
        usd_light.CreateColorAttr(data.color)

    usd_light.CreateIntensityAttr(data.intensity)
    usd_light.CreateInput("transparency", Sdf.ValueTypeNames.Float).Set(data.transparency)

    # # set correct Dome light rotation
    usd_light.AddRotateXOp().Set(180.0)
    usd_light.AddRotateYOp().Set(-90.0)
    # TODO: enable rotation angles


def sync_update(root_prim, world: bpy.types.World):
    stage = root_prim.GetStage()

    world_prim = stage.DefinePrim(root_prim.GetPath().AppendChild(PRIM_NAME))

    if world is None:
        world_prim.SetActive(False)

        return

    if not world_prim.IsActive():
        world_prim.ClearActive()

    for child in world_prim.GetChildren():
        if child.GetName() != Tf.MakeValidIdentifier(world.name):
            child.SetActive(False)

    usd_light = UsdLux.DomeLight.Define(stage,
        Sdf.Path(f"/{PRIM_NAME}").AppendChild(Tf.MakeValidIdentifier(world.name)))
    usd_light.GetPrim().SetActive(True)

    # removing prev settings
    usd_light.CreateColorAttr().Clear()
    usd_light.CreateIntensityAttr().Clear()

    if usd_light.GetTextureFileAttr().Get() is not None:
        usd_light.CreateTextureFileAttr().Clear()

    usd_light.ClearXformOpOrder()

    sync(root_prim, world)


def get_clear_color(root_prim, world: bpy.types.World):
    light_prim = root_prim.GetStage().GetPrimAtPath(root_prim.GetPath().AppendChild(PRIM_NAME).
                                                    AppendChild(Tf.MakeValidIdentifier(world.name)))
    color = light_prim.GetAttribute('inputs:color').Get()
    intensity = light_prim.GetAttribute('inputs:intensity').Get()
    transparency = light_prim.GetAttribute('inputs:transparency').Get()
    clear_color = [c * intensity for c in color]
    clear_color.append(transparency)
    return tuple(clear_color)
