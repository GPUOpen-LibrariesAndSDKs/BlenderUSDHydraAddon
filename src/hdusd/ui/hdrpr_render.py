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
from . import HdUSD_Panel


#
# FINAL RENDER SETTINGS
#
class HDUSD_RENDER_PT_hdrpr_settings_final(HdUSD_Panel):
    bl_label = "RPR Settings"
    bl_parent_id = 'HDUSD_RENDER_PT_render_settings_final'

    @classmethod
    def poll(cls, context):
        return super().poll(context) and context.scene.hdusd.final.delegate == 'HdRprPlugin'

    def draw(self, context):
        hdrpr = context.scene.hdusd.final.hdrpr

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column()
        col.prop(hdrpr, "device")
        col.prop(hdrpr, "render_quality")
        col.prop(hdrpr, "render_mode")


class HDUSD_RENDER_PT_hdrpr_settings_samples_final(HdUSD_Panel):
    bl_label = "Samples"
    bl_parent_id = 'HDUSD_RENDER_PT_hdrpr_settings_final'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        hdrpr = context.scene.hdusd.final.hdrpr

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.prop(hdrpr, "max_samples")

        col = layout.column(align=True)
        col.prop(hdrpr, "variance_threshold")
        row = col.row()
        row.enabled = hdrpr.variance_threshold > 0.0
        row.prop(hdrpr, "min_adaptive_samples")


class HDUSD_RENDER_PT_hdrpr_settings_quality_final(HdUSD_Panel):
    bl_label = "Quality"
    bl_parent_id = 'HDUSD_RENDER_PT_hdrpr_settings_final'
    bl_space_type = 'PROPERTIES'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        hdrpr = context.scene.hdusd.final.hdrpr
        quality = hdrpr.quality

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(align=True)
        col.prop(quality, "max_ray_depth")
        col.prop(quality, "max_ray_depth_diffuse")
        col.prop(quality, "max_ray_depth_glossy")
        col.prop(quality, "max_ray_depth_refraction")
        col.prop(quality, "max_ray_depth_glossy_refraction")

        layout.prop(quality, "raycast_epsilon")

        col = layout.column(align=True)
        col.prop(quality, "enable_radiance_clamping")
        row = col.row()
        row.enabled = quality.enable_radiance_clamping
        row.prop(quality, "radiance_clamping")


class HDUSD_RENDER_PT_hdrpr_settings_denoise_final(HdUSD_Panel):
    bl_label = ""
    bl_parent_id = 'HDUSD_RENDER_PT_hdrpr_settings_final'
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        denoise = context.scene.hdusd.final.hdrpr.denoise
        self.layout.prop(denoise, "enable")

    def draw(self, context):
        denoise = context.scene.hdusd.final.hdrpr.denoise

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.enabled = denoise.enable
        layout.prop(denoise, "min_iter")
        layout.prop(denoise, "iter_step")


#
# VIEWPORT RENDER SETTINGS
#
class HDUSD_RENDER_PT_hdrpr_settings_viewport(HdUSD_Panel):
    bl_label = "RPR Settings"
    bl_parent_id = 'HDUSD_RENDER_PT_render_settings_viewport'

    @classmethod
    def poll(cls, context):
        return super().poll(context) and context.scene.hdusd.viewport.delegate == 'HdRprPlugin'

    def draw(self, context):
        hdrpr = context.scene.hdusd.viewport.hdrpr

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout = layout.column()
        layout.prop(hdrpr, "device")
        layout.prop(hdrpr, "render_quality")
        layout.prop(hdrpr, "render_mode")


class HDUSD_RENDER_PT_hdrpr_settings_samples_viewport(HdUSD_Panel):
    bl_label = "Samples"
    bl_parent_id = 'HDUSD_RENDER_PT_hdrpr_settings_viewport'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        hdrpr = context.scene.hdusd.viewport.hdrpr

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.prop(hdrpr, "max_samples")

        col = layout.column(align=True)
        col.prop(hdrpr, "variance_threshold")
        row = col.row()
        row.enabled = hdrpr.variance_threshold > 0.0
        row.prop(hdrpr, "min_adaptive_samples")


class HDUSD_RENDER_PT_hdrpr_settings_quality_viewport(HdUSD_Panel):
    bl_label = "Quality"
    bl_parent_id = 'HDUSD_RENDER_PT_hdrpr_settings_viewport'
    bl_space_type = 'PROPERTIES'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        hdrpr = context.scene.hdusd.viewport.hdrpr
        quality = hdrpr.interactive_quality

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.prop(quality, "max_ray_depth")
        # layout.prop(quality, "enable_downscale")
        # layout.prop(quality, "resolution_downscale")


class HDUSD_RENDER_PT_hdrpr_settings_denoise_viewport(HdUSD_Panel):
    bl_label = ""
    bl_parent_id = 'HDUSD_RENDER_PT_hdrpr_settings_viewport'
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        denoise = context.scene.hdusd.viewport.hdrpr.denoise
        self.layout.prop(denoise, "enable")

    def draw(self, context):
        denoise = context.scene.hdusd.viewport.hdrpr.denoise

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.enabled = denoise.enable
        layout.prop(denoise, "min_iter")
        layout.prop(denoise, "iter_step")
