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

from pxr import UsdShade


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
                continue

            yield child
            yield from traverse(child)

    yield from traverse(stage.GetPseudoRoot())


def bind_material(mesh_prim, usd_mat):
    bindings = UsdShade.MaterialBindingAPI(mesh_prim)
    bindings.UnbindAllBindings()
    if usd_mat:
        bindings.Bind(usd_mat)
