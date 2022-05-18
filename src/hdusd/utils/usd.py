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

import mathutils
import bpy

from pxr import UsdShade, Gf
from ..utils import log

def get_xform_transform(xform):
    transform = mathutils.Matrix(xform.GetLocalTransformation())
    return transform.transposed()


def set_delegate_variant(prims, name):
    for prim in prims:
        vsets = prim.GetVariantSets()
        if 'delegate' not in vsets.GetNames():
            continue

        vset = vsets.GetVariantSet('delegate')
        vset.SetVariantSelection(name)


def set_delegate_variant_stage(stage, name):
    set_delegate_variant(stage.TraverseAll(), name)


def add_delegate_variants(prim, variants: dict, default_name=None):
    vset = prim.GetVariantSets().AddVariantSet('delegate')
    for name, func in variants.items():
        vset.AddVariant(name)
        vset.SetVariantSelection(name)
        with vset.GetVariantEditContext():
            func()

    if default_name is None:
        default_name = bpy.context.scene.hdusd.viewport.delegate_name

    vset.SetVariantSelection(default_name)


def get_renderer_percent_done(renderer):
    percent = renderer.GetRenderStats().get('percentDone', 0.0)
    if math.isnan(percent):
        percent = 0.0

    return percent


def traverse_stage(stage, *, ignore=None):
    def traverse(prim):
        for child in prim.GetAllChildren():
            if ignore and ignore(child):
                log.warn(f'Ignoring prim {child.GetTypeName()}, {child}')
                continue

            yield child
            yield from traverse(child)

    yield from traverse(stage.GetPseudoRoot())


def bind_material(mesh_prim, usd_mat):
    bindings = UsdShade.MaterialBindingAPI(mesh_prim)
    bindings.UnbindAllBindings()
    if usd_mat:
        bindings.Bind(usd_mat)


def set_timesamples_for_prim(prim, start, end):
    for attr in prim.GetAuthoredAttributes():
        time_samples = attr.GetTimeSamplesInInterval(Gf.Interval(start, end))
        if len(time_samples) > 0:
            nearest_min_sample = min(time_samples, key=lambda x: abs(x - start))
            nearest_max_sample = min(time_samples, key=lambda x: abs(x - end))

            if end > start:
                value = {sample: attr.Get(sample) for sample in time_samples}
            else:
                value = attr.Get(nearest_min_sample)

            attr.Clear()

            if isinstance(value, dict):
                for sample, val in value.items():
                    attr.Set(val, sample)
            else:
                attr.Set(value)

            return nearest_min_sample, nearest_max_sample

        else:
            if value := attr.Get(0):
                attr.Clear()
                attr.Set(value)

            return None, None
    return None, None


def set_timesamples_for_stage(stage, *, is_use_animation, is_restrict_frames, start, end):
    if is_use_animation:
        start_time_code = stage.GetStartTimeCode()
        end_time_code = stage.GetEndTimeCode()

        if is_restrict_frames:
            for prim in stage.TraverseAll():
                min_sample, max_sample = set_timesamples_for_prim(prim, start, end)

                if start == end:
                    stage.ClearMetadata('startTimeCode')
                    stage.ClearMetadata('endTimeCode')
                else:
                    if min_sample and min_sample > start_time_code:
                        start_time_code = min_sample
                        stage.SetMetadata('startTimeCode', min_sample)

                    if max_sample and max_sample < end_time_code:
                        end_time_code = max_sample
                        stage.SetMetadata('endTimeCode', max_sample)

    else:
        stage.ClearMetadata('startTimeCode')
        stage.ClearMetadata('endTimeCode')

        for prim in stage.TraverseAll():
            set_timesamples_for_prim(prim, 0, 0)
