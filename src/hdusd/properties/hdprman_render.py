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
from bpy.props import IntProperty, FloatProperty


class RenderSettings(bpy.types.PropertyGroup):
    samples: IntProperty(
        name="Samples",
        description="Number of samples to render for each pixel",
        min=1, max=2 ** 16,
        default=64,
    )
    variance_threshold: FloatProperty(
        name="Pixel Variance",
        description="Once pixels are below this amount of noise,\n"
                    "no more samples are added. Set to 0 for no cutoff",
        min=0.001, soft_max=0.5,
        default=0.15,
    )
