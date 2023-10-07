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


class RESOLVER_OP_start_live_mode(bpy.types.Operator):
    bl_idname = 'resolver.start_live_mode'
    bl_label = "Connect"
    bl_description = "Connect to Render Studio Resolver server"

    def execute(self, context):
        resolver = context.collection.resolver
        resolver.start_live_mode()
        return {'FINISHED'}


class RESOLVER_OP_stop_live_mode(bpy.types.Operator):
    bl_idname = 'resolver.stop_live_mode'
    bl_label = "Disconnect"
    bl_description = "Disconnect Render Studio Resolver server"

    def execute(self, context):
        resolver = context.collection.resolver
        resolver.stop_live_mode()
        return {'FINISHED'}


class RESOLVER_OP_process_live_update(bpy.types.Operator):
    bl_idname = 'resolver.process_live_mode'
    bl_label = "Process Live Mode"
    bl_description = "Run live update mode"

    def execute(self, context):
        resolver = context.collection.resolver
        resolver.process_live_updates()
        return {'FINISHED'}


class RESOLVER_OP_open_stage_uri(bpy.types.Operator):
    bl_idname = 'resolver.open_stage_uri'
    bl_label = "Open Stage Uri"
    bl_description = "Open USD file using Render Studio Resolver"

    def execute(self, context):
        resolver = context.collection.resolver
        resolver.open_stage()
        return {'FINISHED'}


class RESOLVER_OP_import_stage(bpy.types.Operator):
    bl_idname = 'resolver.import_stage'
    bl_label = "Import Stage"
    bl_description = "Import USD file to Blender"

    def execute(self, context):
        resolver = context.collection.resolver
        resolver.import_stage()
        return {'FINISHED'}


class RESOLVER_OP_export_stage_to_string(bpy.types.Operator):
    bl_idname = 'resolver.export_stage'
    bl_label = "Export Stage to Console"
    bl_description = "Export current USD stage to console"

    def execute(self, context):
        resolver = context.collection.resolver
        print(resolver.get_stage().ExportToString())
        return {'FINISHED'}


register_classes, unregister_classes = bpy.utils.register_classes_factory([
    RESOLVER_OP_start_live_mode,
    RESOLVER_OP_stop_live_mode,
    RESOLVER_OP_process_live_update,
    RESOLVER_OP_open_stage_uri,
    RESOLVER_OP_import_stage,
    RESOLVER_OP_export_stage_to_string,
    ])

def register():
    register_classes()


def unregister():
    unregister_classes()
