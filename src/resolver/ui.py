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


class RESOLVER_PT_object(bpy.types.Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_label = "RenderStudio Connector"

    @classmethod
    def poll(cls, context):
        return context.object

    def draw(self, context):
        resolver = context.object.resolver
        layout = self.layout
        layout.prop(resolver, 'sdf_path')


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
        layout.prop(resolver, 'userId')
        layout.operator("resolver.import_stage")
        layout.operator("resolver.open_stage_uri")
        layout.operator("resolver.start_live_mode")
        layout.operator("resolver.stop_live_mode")
        layout.operator("resolver.process_live_mode")
        layout.separator()
        layout.operator("resolver.export_stage")


register_classes, unregister_classes = bpy.utils.register_classes_factory([
    RESOLVER_PT_collection,
    RESOLVER_PT_object,
    ])

def register():
    register_classes()


def unregister():
    unregister_classes()
