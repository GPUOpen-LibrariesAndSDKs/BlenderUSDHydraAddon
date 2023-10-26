# **********************************************************************
# Copyright 2023 Advanced Micro Devices, Inc
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
# ********************************************************************
from pathlib import Path
import shutil

import bpy
from pxr import Sdf, UsdLux

from ...preferences import preferences

from ... import logging

log = logging.Log('export.world')

SUPPORTED_FORMATS = {".png", ".jpeg", ".jpg", ".hdr", ".tga", ".bmp"}
DEFAULT_FORMAT = ".hdr"
BLENDER_DEFAULT_FORMAT = "HDR"
BLENDER_DEFAULT_COLOR_MODE = "RGB"
READONLY_IMAGE_FORMATS = {".dds"}  # blender can read these formats, but can't write


def get_world_data(world: bpy.types.World):
    data = {'color': (0.05, 0.05, 0.05),
            'image': None,
            'intensity': 1.0,
            'transparency': 1.0}

    if not world:
        return data

    if not world.use_nodes:
        data['color'] = tuple(world.color)
        return data

    output_node = next((node for node in world.node_tree.nodes
                        if node.bl_idname == 'ShaderNodeOutputWorld' and node.is_active_output), None)
    if not output_node:
        return data

    from .nodes import ShaderNodeOutputWorld

    node_parser = ShaderNodeOutputWorld(world, output_node)
    node_item = node_parser.export()
    if not node_item:
        return data

    node_data = node_item.data

    if isinstance(node_data, float):
        data['color'] = (node_data, node_data, node_data)
        return data

    if isinstance(node_data, tuple):
        data['color'] = node_data[:3]
        data['transparency '] = node_data[3]
        return data

    intensity = node_data.get('intensity', 1.0)
    if isinstance(intensity, tuple):
        intensity = intensity[0]

    data['intensity'] = intensity

    color = node_data.get('color')
    if color is None:
        image = node_data.get('image')
        if image:
            data['image'] = cache_image_file(image)

    elif isinstance(color, float):
        data['color'] = (color, color, color)
        data['transparency'] = color

    elif isinstance(color, tuple):
        data['color'] = color[:3]
        data['transparency'] = color[3]

    else:  # dict
        image = color.get('image')
        if image:
            data['image'] = cache_image_file(image)

    return data


def sync(stage, depsgraph):
    world = depsgraph.scene.world
    if not world:
        log.warn("Scene doesn't contain World, nothing to export")
        return

    data = get_world_data(world)

    obj_prim = stage.DefinePrim(stage.GetPseudoRoot().GetPath().AppendChild("World"))
    usd_light = UsdLux.DomeLight.Define(stage, obj_prim.GetPath().AppendChild("World"))
    usd_light.OrientToStageUpAxis()
    usd_light.CreateColorAttr(data['color'])
    usd_light.CreateIntensityAttr(data['intensity'])
    usd_light.GetPrim().CreateAttribute("inputs:transparency", Sdf.ValueTypeNames.Float).Set(data['transparency'])

    if not data['image']:
        return

    tex_attr = usd_light.CreateTextureFileAttr()
    tex_attr.ClearDefault()
    tex_attr.Set(str(data['image']))

    # set correct Dome light rotation
    usd_light.AddRotateYOp().Set(-90.0)


def cache_image_file(image: bpy.types.Image):
    root_dir = Path(preferences().rs_workspace_dir) / bpy.context.scene.hydra_rpr.render_studio.channel
    world_dir = root_dir / "textures/world"
    image_path = Path(image.filepath_from_user())

    if not image.packed_file and image.source != 'GENERATED':
        if not image_path.is_file():
            log.warn("Image is missing", image, image_path)

            return None

        image_suffix = image_path.suffix.lower()

        if image_suffix in READONLY_IMAGE_FORMATS or (
                image_suffix in SUPPORTED_FORMATS and
                f".{image.file_format.lower()}" in SUPPORTED_FORMATS and not image.is_dirty):
            filepath = world_dir / image_path.name
            shutil.copy(image_path, filepath)
            return filepath.relative_to(root_dir)

    filename = image_path.stem if image_path.stem else image.name
    filename += DEFAULT_FORMAT
    filepath = world_dir / filename

    scene = bpy.context.scene
    user_format = scene.render.image_settings.file_format
    user_color_mode = scene.render.image_settings.color_mode

    if not user_color_mode:
        user_color_mode = BLENDER_DEFAULT_COLOR_MODE

    scene.render.image_settings.file_format = BLENDER_DEFAULT_FORMAT
    scene.render.image_settings.color_mode = BLENDER_DEFAULT_COLOR_MODE

    try:
        image.save_render(filepath=str(filepath))

    except Exception as err:
        log.warn("Image isn't exported'", image, filepath, err)
        return None

    finally:
        scene.render.image_settings.file_format = user_format
        scene.render.image_settings.color_mode = user_color_mode

    return filepath.relative_to(root_dir)
