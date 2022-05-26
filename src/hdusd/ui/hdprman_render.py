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
class HDUSD_RENDER_PT_hdprman_settings_final(HdUSD_Panel):
    bl_label = "RenderMan Settings"
    bl_parent_id = 'HDUSD_RENDER_PT_render_settings_final'

    @classmethod
    def poll(cls, context):
        return super().poll(context) and context.scene.hdusd.final.delegate == 'HdPrmanLoaderRendererPlugin'

    def draw(self, context):
        pass


class HDUSD_RENDER_PT_hdprman_settings_samples_final(HdUSD_Panel):
    bl_label = "Samples"
    bl_parent_id = 'HDUSD_RENDER_PT_hdprman_settings_final'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        hdprman = context.scene.hdusd.final.hdprman

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(align=True)
        col.prop(hdprman, "samples")
        col.prop(hdprman, "variance_threshold")
        col.prop(hdprman, "timeout")


#
# VIEWPORT RENDER SETTINGS
#
class HDUSD_RENDER_PT_hdprman_settings_viewport(HdUSD_Panel):
    bl_label = "RenderMan Settings"
    bl_parent_id = 'HDUSD_RENDER_PT_render_settings_viewport'

    @classmethod
    def poll(cls, context):
        return super().poll(context) and context.scene.hdusd.viewport.delegate == 'HdPrmanLoaderRendererPlugin'

    def draw(self, context):
        pass


class HDUSD_RENDER_PT_hdprman_settings_samples_viewport(HdUSD_Panel):
    bl_label = "Samples"
    bl_parent_id = 'HDUSD_RENDER_PT_hdprman_settings_viewport'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        hdprman = context.scene.hdusd.viewport.hdprman

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(align=True)
        col.prop(hdprman, "samples")
        col.prop(hdprman, "variance_threshold")
        col.prop(hdprman, "timeout")
