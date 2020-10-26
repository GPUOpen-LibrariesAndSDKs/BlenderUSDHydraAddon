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

from ..utils import logging
log = logging.Log(tag='properties')


class HdUSDProperties(bpy.types.PropertyGroup):
    bl_type = None

    @classmethod
    def register(cls):
        log("Register", cls)
        cls.bl_type.hdusd = bpy.props.PointerProperty(
            name="HdUSD properties",
            description="HdUSD properties",
            type=cls,
        )

    @classmethod
    def unregister(cls):
        log("Unregister", cls)
        del cls.bl_type.hdusd


from . import scene, object
register, unregister = bpy.utils.register_classes_factory((
    scene.RenderDelegate,
    scene.SceneProperties,

    object.ObjectProperties
))
