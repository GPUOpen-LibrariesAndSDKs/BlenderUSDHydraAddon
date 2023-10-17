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

from .resolver import rs_resolver


class RESOLVER_OP_connect(bpy.types.Operator):
    bl_idname = 'render_studio.connect'
    bl_label = "Connect"
    bl_description = "Connect to AMD RenderStudio"

    def execute(self, context):
        rs_resolver.connect()

        return {'FINISHED'}


class RESOLVER_OP_disconnect(bpy.types.Operator):
    bl_idname = 'render_studio.disconnect'
    bl_label = "Disconnect"
    bl_description = "Disconnect AMD RenderStudio"

    def execute(self, context):
        rs_resolver.disconnect()
        return {'FINISHED'}


class RESOLVER_OP_sync_scene(bpy.types.Operator):
    bl_idname = 'render_studio.sync_scene'
    bl_label = "Sync Scene"
    bl_description = "Sync scene to Usd file"

    def execute(self, context):
        rs_resolver.sync_scene()
        return {'FINISHED'}


class RESOLVER_OP_start_live_sync(bpy.types.Operator):
    bl_idname = 'render_studio.start_live_sync'
    bl_label = "Start Live Sync"
    bl_description = "Start syncing scene every update"

    def execute(self, context):
        rs_resolver.start_live_sync()
        return {'FINISHED'}


class RESOLVER_OP_stop_live_sync(bpy.types.Operator):
    bl_idname = 'render_studio.stop_live_sync'
    bl_label = "Stop Live Sync"
    bl_description = "Stop syncing scene every update"

    def execute(self, context):
        rs_resolver.stop_live_sync()
        return {'FINISHED'}


class RESOLVER_OP_export_stage_to_string(bpy.types.Operator):
    bl_idname = 'render_studio.export_stage'
    bl_label = "Export Stage to Console"
    bl_description = "Export current USD stage to console"

    def execute(self, context):
        print(rs_resolver.stage.ExportToString())
        return {'FINISHED'}


register_classes, unregister_classes = bpy.utils.register_classes_factory([
    RESOLVER_OP_connect,
    RESOLVER_OP_disconnect,
    RESOLVER_OP_sync_scene,
    RESOLVER_OP_start_live_sync,
    RESOLVER_OP_stop_live_sync,
    # RESOLVER_OP_export_stage_to_string,
])


def register():
    register_classes()


def unregister():
    unregister_classes()
