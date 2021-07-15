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
import math
import numpy as np

from pxr import UsdLux, Tf
import bpy


from ..utils import logging
log = logging.Log(tag='export.light')


def get_radiant_power(light: bpy.types.Light, is_gl_mode):
    """ Return light radiant power depending on light type """

    # calculating color intensity
    color = np.array(light.color)
    intensity = color * light.energy
    if is_gl_mode:
        # HdStorm results are about 50-100 times brighter than HdRPR one
        intensity /= 1000

    # calculating radian power for core
    if light.type == 'POINT':
        if is_gl_mode:
            return intensity

        # point light is a small sphere, adjust intensity to normalize it
        area = 4 * math.pi * pow(light.shadow_soft_size / 0.75, 2)  # coefficient approximated to follow Cycles results
        return intensity / area

    elif light.type == 'SUN':
        return intensity * 0.000025  # coefficient approximated to follow Cycles results with RPR render engine

    elif light.type == 'AREA':
        area = 1
        if light.shape == 'SQUARE':
            area = light.size * light.size
        elif light.shape == 'RECTANGLE':
            area = light.size * light.size_y
        elif light.shape == 'DISK':
            area = math.pi * light.size * light.size
        else:
            # roughly approximated ellipse area
            area = math.pi * light.size * light.size_y

        intensity /= area

    return intensity


def sync(obj_prim, obj: bpy.types.Object, **kwargs):
    """ Creates pyrpr.Light from obj.data: bpy.types.Light """
    light = obj.data
    stage = obj_prim.GetStage()
    is_gl_mode = kwargs.get('is_gl_delegate', False)
    is_preview_render = kwargs.get('is_preview_render', False)
    log("sync", light, obj)

    light_path = obj_prim.GetPath().AppendChild(Tf.MakeValidIdentifier(light.name))

    if light.type == 'POINT':
        usd_light = UsdLux.SphereLight.Define(stage, light_path)

        size = light.shadow_soft_size
        usd_light.CreateRadiusAttr(size)

    elif light.type in ('SUN', 'HEMI'):  # just in case old scenes will have outdated Hemi
        if is_gl_mode:
            log.warn(f"Unsupported in GL mode Sun light '{obj.name}' skipped")
            return

        usd_light = UsdLux.DistantLight.Define(stage, light_path)
        angle = math.degrees(light.angle)
        usd_light.CreateAngleAttr(angle)
        # TODO skip for HdStorm as unsupported

    elif light.type == 'SPOT':
        log.warn(f"Unsupported Spot light '{obj.name}' skipped")
        # TODO find a way to emulate Spot light in USD
        return

    elif light.type == 'AREA':
        shape_type = light.shape

        if shape_type == 'SQUARE':
            usd_light = UsdLux.RectLight.Define(stage, light_path)
            usd_light.CreateWidthAttr(light.size)
            usd_light.CreateHeightAttr(light.size)

        elif shape_type == 'RECTANGLE':
            usd_light = UsdLux.RectLight.Define(stage, light_path)
            usd_light.CreateWidthAttr(light.size)
            usd_light.CreateHeightAttr(light.size_y)

        elif shape_type == 'DISK':
            if is_gl_mode:
                # Disk light is unsupported by HdStorm, using square Rectangular light of the similar area instead
                usd_light = UsdLux.RectLight.Define(stage, light_path)
                size = 0.886 * light.size
                usd_light.CreateWidthAttr(size)
                usd_light.CreateHeightAttr(size)
            else:
                usd_light = UsdLux.DiskLight.Define(stage, light_path)
                usd_light.CreateRadiusAttr(light.size)

        else:  # shape_type == 'ELLIPSE':
            # Using Rectangular light of the approximately similar area instead
            usd_light = UsdLux.RectLight.Define(stage, light_path)
            usd_light.CreateWidthAttr(0.886 * light.size)
            usd_light.CreateHeightAttr(0.886 * light.size_y)
            # TODO use custom ellipse-shaped mesh instead

    else:
        raise ValueError("Unsupported light type", light, light.type)

    power = get_radiant_power(light, is_gl_mode)

    # Material Previews are overly bright, that's why
    # decreasing light intensity for material preview by 10 times
    if is_preview_render:
        power *= 0.1

    usd_light.CreateColorAttr(tuple(power))


def sync_update(obj_prim, obj: bpy.types.Object, **kwargs):
    """ Update existing light from obj.data: bpy.types.Light or create a new light """
    light = obj.data
    log("sync_update", light, obj)

    stage = obj_prim.GetStage()
    for child_prim in obj_prim.GetAllChildren():
        stage.RemovePrim(child_prim.GetPath())

    sync(obj_prim, obj, **kwargs)
