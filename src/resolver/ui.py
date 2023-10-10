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


class RESOLVER_PT_collection(bpy.types.Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'collection'
    bl_label = "RenderStudio Connector"

    def draw(self, context):
        resolver = context.collection.resolver
        layout = self.layout
        layout.prop(resolver, 'usd_path')
        layout.prop(resolver, 'liveUrl')
        layout.prop(resolver, 'storageUrl')
        layout.prop(resolver, 'channelId')
        if resolver.is_connected:
            layout.operator("resolver.disconnect")

        else:
            layout.operator("resolver.connect")

        layout.separator()
        layout.operator("resolver.export_stage")


register_classes, unregister_classes = bpy.utils.register_classes_factory([
    RESOLVER_PT_collection,
    ])

def register():
    register_classes()


def unregister():
    unregister_classes()
