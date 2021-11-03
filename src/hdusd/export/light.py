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

from pxr import UsdLux, Tf, Sdf
import bpy


from ..utils import logging
log = logging.Log('export.light')


def get_radiant_power(light: bpy.types.Light):
    """ Return light radiant power depending on light type """

    # calculating color intensity
    color = np.array(light.color)
    intensity = color * light.energy

    if light.type == 'POINT':
        return intensity * 4            # coefficient approximated to follow Cycles results

    elif light.type == 'SPOT':
        return intensity

    elif light.type == 'SUN':
        return intensity * 0.000025     # coefficient approximated to follow Cycles results

    elif light.type == 'AREA':
        area = 1.0
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
    context = bpy.context
    is_preview_render = kwargs.get('is_preview_render', False)
    log("sync", light, obj)

    light_path = obj_prim.GetPath().AppendChild(Tf.MakeValidIdentifier(light.name))

    if light.type == 'POINT':
        usd_light = UsdLux.SphereLight.Define(stage, light_path)

        size = light.shadow_soft_size
        usd_light.CreateRadiusAttr(size)

    elif light.type in ('SUN', 'HEMI'):  # just in case old scenes will have outdated Hemi
        usd_light = UsdLux.DistantLight.Define(stage, light_path)
        angle = math.degrees(light.angle)
        usd_light.CreateAngleAttr(angle)
        usd_light.CreateIntensityAttr(light.energy)

    elif light.type == 'SPOT':
        usd_light = UsdLux.SphereLight.Define(stage, light_path)
        usd_prim = stage.GetPrimAtPath(light_path)

        usd_light.CreateTreatAsPointAttr(1)

        spot_size = math.degrees(light.spot_size)

        usd_shaping = UsdLux.ShapingAPI(usd_prim)
        usd_shaping.CreateShapingConeAngleAttr(spot_size / 2)
        usd_shaping.CreateShapingConeSoftnessAttr(light.spot_blend)

        usd_shaping.Apply(usd_prim)

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
            usd_light = UsdLux.DiskLight.Define(stage, light_path)
            usd_light.CreateRadiusAttr(light.size)

        else:  # shape_type == 'ELLIPSE':
            usd_light = UsdLux.DiskLight.Define(stage, light_path)
            usd_light.CreateRadiusAttr(light.size)

    else:
        raise ValueError("Unsupported light type", light, light.type)

    power = get_radiant_power(light)

    colorAttr = usd_light.CreateColorAttr()

    if is_preview_render:
        # Material Previews are overly bright, that's why
        # decreasing light intensity for material preview by 10 times
        power *= 0.1
        colorAttr.Set(tuple(power))

    else:
        # setting light color through variants for GL and RPR renderers
        vset = obj_prim.GetVariantSets().AddVariantSet('delegate')
        vset.AddVariant('GL')
        vset.AddVariant('RPR')

        vset.SetVariantSelection('GL')
        with vset.GetVariantEditContext():
            colorAttr.Set(tuple(power / 1000))

        vset.SetVariantSelection('RPR')
        with vset.GetVariantEditContext():
            colorAttr.Set(tuple(power))

        # setting default variant
        vset.SetVariantSelection('GL' if context.scene.hdusd.viewport.is_gl_delegate else 'RPR')


def sync_update(obj_prim, obj: bpy.types.Object, **kwargs):
    """ Update existing light from obj.data: bpy.types.Light or create a new light """
    light = obj.data
    log("sync_update", light, obj)

    stage = obj_prim.GetStage()
    for child_prim in obj_prim.GetAllChildren():
        stage.RemovePrim(child_prim.GetPath())

    sync(obj_prim, obj, **kwargs)
