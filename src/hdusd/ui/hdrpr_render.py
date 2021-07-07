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
        layout.prop(hdrpr, "render_mode")


class HDUSD_RENDER_PT_hdrpr_settings_samples_viewport(HdUSD_Panel):
    bl_label = "Samples"
    bl_parent_id = 'HDUSD_RENDER_PT_hdrpr_settings_viewport'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        hdrpr = context.scene.hdusd.final.hdrpr

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.prop(hdrpr, "min_adaptive_samples")
        layout.prop(hdrpr, "max_samples")
        layout.prop(hdrpr, "variance_threshold")


class HDUSD_RENDER_PT_hdrpr_settings_quality_viewport(HdUSD_Panel):
    bl_label = "Quality"
    bl_parent_id = 'HDUSD_RENDER_PT_hdrpr_settings_viewport'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        hdrpr = context.scene.hdusd.final.hdrpr
        quality = hdrpr.interactive_quality

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.prop(hdrpr, "render_quality")
        layout.prop(quality, "max_ray_depth")
        layout.prop(quality, "enable_downscale")
        layout.prop(quality, "resolution_downscale")
