# **********************************************************************
# Copyright 2023 Advanced Micro Devices, Inc
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
import bpy


class RS_RESOLVER_PT_resolver(bpy.types.Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'render'
    bl_label = "RenderStudio Resolver"

    def draw(self, context):
        resolver = context.collection.resolver
        layout = self.layout
        if resolver.is_connected:
            layout.operator("resolver.disconnect")

        else:
            layout.operator("resolver.connect")

        layout.separator()
        layout.operator("resolver.export_stage")

def draw_button(self, context):
    resolver = context.collection.resolver
    if resolver.is_connected:
        self.layout.operator("resolver.disconnect")

    else:
        self.layout.operator("resolver.connect")


register_classes, unregister_classes = bpy.utils.register_classes_factory([
    RS_RESOLVER_PT_resolver,
    ])

def register():
    register_classes()
    bpy.types.OUTLINER_HT_header.prepend(draw_button)


def unregister():
    unregister_classes()
    bpy.types.OUTLINER_HT_header.remove(draw_button)
