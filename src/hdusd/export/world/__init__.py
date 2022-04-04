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
from pathlib import Path
import math

import bpy

from pxr import Sdf, UsdLux, Tf

from ...utils.image import cache_image_file, cache_image_file_path
from ...utils import BLENDER_DATA_DIR
from ...utils import usd as usd_utils

from ...utils import logging
log = logging.Log('export.world')


OBJ_PRIM_NAME = "World"
LIGHT_PRIM_NAME = "World"


@dataclass(init=False, eq=True)
class ShadingData:
    type: str
    use_scene_lights: bool = True
    use_scene_world: bool = True
    has_world: bool = False
    studiolight: Path = None
    studiolight_rotate_z: float = 0.0
    studiolight_background_alpha: float = 0.0
    studiolight_intensity: float = 1.0

    def __init__(self, context: bpy.types.Context, world: bpy.types.World):
        shading = context.area.spaces.active.shading

        self.type = shading.type
        if self.type == 'RENDERED':
            self.use_scene_lights = shading.use_scene_lights_render
            self.use_scene_world = shading.use_scene_world_render
        else:
            self.use_scene_lights = shading.use_scene_lights
            self.use_scene_world = shading.use_scene_world

        if self.use_scene_world:
            self.has_world = bool(world)

        else:
            if shading.selected_studio_light.path:
                self.studiolight = Path(shading.selected_studio_light.path)
            else:
                self.studiolight = BLENDER_DATA_DIR / "studiolights/world" / shading.studio_light

            self.studiolight_rotate_z = shading.studiolight_rotate_z
            self.studiolight_background_alpha = shading.studiolight_background_alpha
            self.studiolight_intensity = shading.studiolight_intensity


@dataclass(init=False, eq=True, repr=True)
class WorldData:
    """ Comparable dataclass which holds all environment settings """

    color: tuple = (0.05, 0.05, 0.05)
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
    def init_from_shading(shading: ShadingData, world):
        if shading.use_scene_world:
            return WorldData.init_from_world(world)

        data = WorldData()
        data.intensity = shading.studiolight_intensity
        data.rotation = (0.0, 0.0, shading.studiolight_rotate_z)
        data.image = cache_image_file_path(shading.studiolight)
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


def sync(root_prim, world: bpy.types.World, shading: ShadingData = None):
    if shading:
        data = WorldData.init_from_shading(shading, world)
    else:
        data = WorldData.init_from_world(world)

    stage = root_prim.GetStage()

    obj_prim = stage.DefinePrim(root_prim.GetPath().AppendChild(OBJ_PRIM_NAME))
    usd_light = UsdLux.DomeLight.Define(stage, obj_prim.GetPath().AppendChild(LIGHT_PRIM_NAME))
    light_prim = usd_light.GetPrim()
    usd_light.OrientToStageUpAxis()

    if data.image:
        tex_attr = usd_light.CreateTextureFileAttr()
        tex_attr.ClearDefault()
        usd_utils.add_delegate_variants(obj_prim, {
            'GL': lambda: tex_attr.Set(""),
            'RPR': lambda: tex_attr.Set(str(data.image))
        })

    usd_light.CreateColorAttr(data.color)

    usd_light.CreateIntensityAttr(data.intensity)
    light_prim.CreateAttribute("inputs:transparency", Sdf.ValueTypeNames.Float).Set(data.transparency)

    # set correct Dome light rotation
    usd_light.AddRotateXOp().Set(180.0)
    usd_light.AddRotateYOp().Set(-90.0 + math.degrees(data.rotation[2]))


def sync_update(root_prim, world: bpy.types.World, shading: ShadingData = None):
    stage = root_prim.GetStage()
    usd_light = UsdLux.DomeLight.Define(
        stage, root_prim.GetPath().AppendChild(OBJ_PRIM_NAME).AppendChild(LIGHT_PRIM_NAME))

    # removing prev settings
    usd_light.CreateColorAttr().Clear()
    usd_light.CreateIntensityAttr().Clear()

    if usd_light.GetTextureFileAttr().Get() is not None:
        usd_light.GetTextureFileAttr().Block()

    usd_light.ClearXformOpOrder()

    sync(root_prim, world, shading)


def get_clear_color(root_prim):
    light_prim = root_prim.GetChild(OBJ_PRIM_NAME).GetChild(LIGHT_PRIM_NAME)
    color = light_prim.GetAttribute('inputs:color').Get()
    intensity = light_prim.GetAttribute('inputs:intensity').Get()
    transparency = light_prim.GetAttribute('inputs:transparency').Get()
    clear_color = [c * intensity for c in color]
    clear_color.append(transparency)
    return tuple(clear_color)
