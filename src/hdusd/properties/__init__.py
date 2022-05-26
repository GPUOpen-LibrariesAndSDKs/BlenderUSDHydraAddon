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
import bpy

from ..utils import stage_cache

from ..utils import logging
log = logging.Log('properties')


class HdUSDProperties(bpy.types.PropertyGroup):
    bl_type = None

    @classmethod
    def register(cls):
        cls.bl_type.hdusd = bpy.props.PointerProperty(
            name="HdUSD properties",
            description="HdUSD properties",
            type=cls,
        )

    @classmethod
    def unregister(cls):
        del cls.bl_type.hdusd


class CachedStageProp(bpy.types.PropertyGroup, stage_cache.CachedStage):
    id: bpy.props.IntProperty(default=stage_cache.ID_NO_STAGE)
    is_owner: bpy.props.BoolProperty(default=False)

    def __del__(self):
        pass


from . import (
    scene,
    object,
    node,
    usd_list,
    material,
    hdrpr_render,
    hdprman_render,
    matlib
)
register, unregister = bpy.utils.register_classes_factory((
    CachedStageProp,

    hdrpr_render.QualitySettings,
    hdrpr_render.InteractiveQualitySettings,
    hdrpr_render.ContourSettings,
    hdrpr_render.DenoiseSettings,
    hdrpr_render.RenderSettings,

    hdprman_render.RenderSettings,

    usd_list.PrimPropertyItem,
    usd_list.UsdListItem,
    usd_list.UsdList,

    node.NodeProperties,

    scene.FinalRenderSettings,
    scene.ViewportRenderSettings,
    scene.SceneProperties,

    object.ObjectProperties,

    material.MaterialProperties,

    matlib.MatlibProperties,
    matlib.WindowManagerProperties,
))
