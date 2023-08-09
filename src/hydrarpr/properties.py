# **********************************************************************
# Copyright 2022 Advanced Micro Devices, Inc
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
import math

import bpy
from bpy.props import (
    PointerProperty,
    EnumProperty,
    FloatProperty,
    BoolProperty,
    IntProperty,
)


class Properties(bpy.types.PropertyGroup):
    bl_type = None

    @classmethod
    def register(cls):
        cls.bl_type.hydra_rpr = bpy.props.PointerProperty(
            name="Hydra RPR",
            description="Hydra RPR properties",
            type=cls,
        )

    @classmethod
    def unregister(cls):
        del cls.bl_type.hydra_rpr


class QualitySettings(bpy.types.PropertyGroup):
    max_ray_depth: IntProperty(
        name="Max Ray Depth",
        description="The number of times that a ray bounces off various surfaces "
                    "before being terminated",
        min=1, max=50,
        default=8,
    )
    max_ray_depth_diffuse: IntProperty(
        name="Diffuse Ray Depth",
        description="The maximum number of times that a light ray can be bounced off diffuse surfaces",
        min=0, max=50,
        default=3,
    )
    max_ray_depth_glossy: IntProperty(
        name="Glossy Ray Depth",
        description="The maximum number of ray bounces from specular surfaces",
        min=0, max=50,
        default=3,
    )
    max_ray_depth_refraction: IntProperty(
        name="Refraction Ray Depth",
        description="The maximum number of times that a light ray can be refracted, and is\n"
                    "designated for clear transparent materials, such as glass",
        min=0, max=50,
        default=3,
    )
    max_ray_depth_glossy_refraction: IntProperty(
        name="Glossy Refraction Ray Depth",
        description="The Glossy Refraction Ray Depth parameter is similar to the Refraction Ray Depth.\n"
                    "The difference is that it is aimed to work with matte refractive materials,\n"
                    "such as semi-frosted glass",
        min=0, max=50,
        default=3,
    )
    max_ray_depth_shadow: IntProperty(
        name="Shadow Ray Depth",
        description="Controls the accuracy of shadows cast by transparent objects.\n"
                    "It defines the maximum number of surfaces that a light ray can encounter on\n"
                    "its way causing these surfaces to cast shadows",
        min=0, max=50,
        default=2,
    )
    raycast_epsilon: FloatProperty(
        name="Ray Cast Epsilon",
        description="Determines an offset used to move light rays away from the geometry for\n"
                    "ray-surface intersection calculations",
        subtype='DISTANCE',
        min=1e-6, max=1.0,
        default=2e-3,
    )
    enable_radiance_clamping: BoolProperty(
        name="Clamp Fireflies",
        description="Clamp Fireflies",
        default=False,
    )
    radiance_clamping: FloatProperty(
        name="Max Radiance",
        description="Limits the intensity or the maximum brightness of samples in the scene.\n"
                    "Greater clamp radiance values produce more brightness. Set to 0 ot disable clamping",
        min=0.0, max=1e6,
        default=0.0,
    )
    pixel_filter_width: FloatProperty(
        name="Width",
        description="Pixel filter width",
        min=0.0, max=5.0,
        default=1.5,
    )


class InteractiveQualitySettings(bpy.types.PropertyGroup):
    max_ray_depth: IntProperty(
        name="Max Ray Depth",
        description="Controls value of 'Max Ray Depth' in interactive mode",
        min=1, max=50,
        default=2,
    )
    enable_downscale: BoolProperty(
        name="Downscale Resolution",
        description="Controls whether in interactive mode resolution should be downscaled or no",
        default=True,
    )
    resolution_downscale: IntProperty(
        name="Resolution Downscale",
        description="Controls how much rendering resolution is downscaled in interactive mode.\n"
                    "Formula: resolution / (2 ^ downscale). E.g. downscale==2 will give you 4 times\n"
                    "smaller rendering resolution",
        min=0, max=10,
        default=3,
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


class DenoiseSettings(bpy.types.PropertyGroup):
    enable: BoolProperty(
        name="AI Denoising",
        description="Enable AI Denoising",
        default=False,
    )
    min_iter: IntProperty(
        name="Min Iteration",
        description="The first iteration on which denoising should be applied",
        min=1, max=2 ** 16,
        default=4,
    )
    iter_step: IntProperty(
        name="Iteration Step",
        description="Denoise use frequency. To denoise on each iteration, set to 1",
        min=1, max=2 ** 16,
        default=32,
    )


class RenderSettings(bpy.types.PropertyGroup):
    device: EnumProperty(
        name="Render Device",
        description="Render Device",
        items=(('GPU', "GPU", "GPU render device"),
               ('CPU', "CPU", "Legacy render device")),
        default='GPU',
    )
    render_quality: EnumProperty(
        name="Render Quality",
        description="Render Quality",
        items=(
            ('Northstar', "Full", "Full render quality"),
            ('HybridPro', "Interactive", "Interactive render quality"),
        ),
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
    max_samples: IntProperty(
        name="Max Samples",
        description="Maximum number of samples to render for each pixel",
        min=1, max=2 ** 16,
        default=256,
    )
    min_adaptive_samples: IntProperty(
        name="Min Samples",
        description="Minimum number of samples to render for each pixel. After this, adaptive sampling\n"
                    "will stop sampling pixels where noise is less than 'Variance Threshold'",
        min=1, max=2 ** 16,
        default=64,
    )
    variance_threshold: FloatProperty(
        name="Noise Threshold",
        description="Cutoff for adaptive sampling. Once pixels are below this amount of noise,\n"
                    "no more samples are added. Set to 0 for no cutoff",
        min=0.0, max=1.0,
        default=0.05,
    )
    enable_alpha: BoolProperty(
        name="Enable Color Alpha",
        description="World background is transparent, for compositing the render over another background",
        default=False,
    )
    enable_motion_blur: BoolProperty(
        name="Enable Beauty Motion Blur",
        description="If disabled, only velocity AOV will store information about movement on the scene.\n"
                    "Required for motion blur that is generated in post-processing",
        default=True,
    )

    quality: PointerProperty(type=QualitySettings)
    interactive_quality: PointerProperty(type=InteractiveQualitySettings)

    contour: PointerProperty(type=ContourSettings)
    denoise: PointerProperty(type=DenoiseSettings)


class SceneProperties(Properties):
    bl_type = bpy.types.Scene

    final: bpy.props.PointerProperty(type=RenderSettings)
    viewport: bpy.props.PointerProperty(type=RenderSettings)


register, unregister = bpy.utils.register_classes_factory((
    ContourSettings,
    DenoiseSettings,
    InteractiveQualitySettings,
    QualitySettings,
    RenderSettings,
    SceneProperties,
))
