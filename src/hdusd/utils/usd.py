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


def get_xform_transform(xform):
    transform = mathutils.Matrix(xform.GetLocalTransformation())
    return transform.transposed()


def set_variant_delegate(stage, is_gl_delegate):
    name = 'GL' if is_gl_delegate else 'RPR'
    for prim in stage.TraverseAll():
        vsets = prim.GetVariantSets()
        if 'delegate' not in vsets.GetNames():
            continue

        vset = vsets.GetVariantSet('delegate')
        vset.SetVariantSelection(name)


def get_renderer_percent_done(renderer):
    percent = renderer.GetRenderStats().get('percentDone', 0.0)
    if math.isnan(percent):
        percent = 0.0

    return percent


def set_delegate_variants(obj_prim, gl_func, rpr_func):
    vset = obj_prim.GetVariantSets().AddVariantSet('delegate')
    vset.AddVariant('GL')
    vset.AddVariant('RPR')

    vset.SetVariantSelection('GL')
    with vset.GetVariantEditContext():
        gl_func()

    vset.SetVariantSelection('RPR')
    with vset.GetVariantEditContext():
        rpr_func()

    # setting default variant
    vset.SetVariantSelection('GL' if bpy.context.scene.hdusd.viewport.is_gl_delegate else 'RPR')
