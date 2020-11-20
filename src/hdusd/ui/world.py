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

from cycles.ui import panel_node_draw

from . import HdUSD_Panel


class HDUSD_WORLD_PT_preview(HdUSD_Panel):
    bl_label = "Preview"
    bl_context = "world"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.world and super().poll(context)

    def draw(self, context):
        self.layout.template_preview(context.world)


class HDUSD_WORLD_PT_surface(HdUSD_Panel):
    bl_label = "Surface"
    bl_context = "world"

    @classmethod
    def poll(cls, context):
        return context.world and super().poll(context)

    def draw(self, context):
        layout = self.layout

        layout.use_property_split = True

        world = context.world

        if not panel_node_draw(layout, world, 'OUTPUT_WORLD', 'Surface'):
            layout.prop(world, "color")

