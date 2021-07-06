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

import bpy
from bpy.types import (
    PointerProperty,
    EnumProperty,
    FloatProperty,
    BoolProperty,
)


class ContourSettings(bpy.types.PropertyGroup):
    antialiasing: FloatProperty(
        name="Antialiasing",
        description="Contour Antialising",
        min=0.0, max=1.0,
        default=1.0,
    )
    use_normal: BoolProperty(
        name="Use Normal",
        description="Whether to use geometry normals for edge detection or not",
        default=True,
    )
    line_width_normal: FloatProperty(
        name="Line Width Normal",
        description="Line width of edges detected via normals",
        min=1.0, max=100.0,
        default=1.0,
    )
    normal_threshold: FloatProperty(
        name="Normal Threshold",
        description="Threshold for normals, in degrees",
        subtype='ANGLE',
        min=0.0, max=math.radians(180.0),
        default=math.radians(45.0),
    )
    use_prim_id: BoolProperty(
        name="Use Primitive ID",
        description="Whether to use primitive Id for edge detection or not",
        default=True,
    )
    line_width_prim_id: FloatProperty(
        name="Line Primitive Id",
        description="Line width of edges detected via primitive Id",
        min=0.0, max=100.0,
        default=1.0,
    )
    use_material_id: BoolProperty(
        name="Use Material Id",
        description="Whether to use material Id for edge detection or not",
        default=True,
    )
    line_width_material_id: FloatProperty(
        name="Line Width Material Id",
        description="Line width of edges detected via material Id",
        min=0.0, max=100.0,
        default=1.0,
    )
    debug: BoolProperty(
        name="Debug",
        description="""Whether to show colored outlines according to used features or not.
Colors legend:
 * red - primitive Id
 * green - material Id
 * blue - normal
 * yellow - primitive Id + material Id
 * magenta - primitive Id + normal
 * cyan - material Id + normal
 * black - all""",
        default=True,
    )


class RenderSettings(bpy.types.PropertyGroup):
    render_quality: EnumProperty(
        name="Renderer Quality",
        description="",
        items=(('Northstar', "Full", "Full render quality"),
               ('Full', "Legacy", "Legacy render quality"),
               ('High', "High", "High render quality"),
               ('Medium', "Medium", "Medium render quality"),
               ('Low', "Low", "Low render quality")),
        default='Northstar',
    )
    render_mode: EnumProperty(
        name="Render Mode",
        description="Override render mode",
        items=(
            ('Global Illumination', "Global Illumination", "Global illumination render mode"),
            ('Direct Illumination', "Direct Illumination", "Direct illumination render mode"),
            ('Wireframe', "Wireframe", "Wireframe render mode"),
            ('Material Index', "Material Index", "Material index render mode"),
            ('Position', "Position", "World position render mode"),
            ('Normal', "Normal", "Shading normal render mode"),
            ('Texcoord', "Texture Coordinate", "Texture coordinate render mode"),
            ('Ambient Occlusion', "Ambient Occlusion", "Ambient occlusion render mode"),
            ('Diffuse', "Diffuse", "Diffuse render mode"),
            ('Contour', "Contour", "Contour render mode"),
        ),
        default='Global Illumination',
    )
    ao_radius: FloatProperty(
        name="AO Radius",
        description="Ambient Occlusion Radius",
        min=0.0, max=100.0,
        default=1.0,
    )
    contour: PointerProperty(type=ContourSettings)
