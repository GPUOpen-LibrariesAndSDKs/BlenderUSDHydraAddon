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
from .ui import tag_redraw
from ..preferences import preferences


class RESOLVER_OP_connect(bpy.types.Operator):
    bl_idname = 'render_studio.connect'
    bl_label = "Connect"
    bl_description = "Connect to AMD RenderStudio"

    @classmethod
    def poll(cls, context):
        pref = preferences()
        return pref.rs_workspace_dir and pref.rs_workspace_url

    def execute(self, context):
        rs_resolver.connect()
        tag_redraw()

        return {'FINISHED'}


class RESOLVER_OP_disconnect(bpy.types.Operator):
    bl_idname = 'render_studio.disconnect'
    bl_label = "Disconnect"
    bl_description = "Disconnect from AMD RenderStudio"

    @classmethod
    def poll(cls, context):
        return rs_resolver.is_connected

    def execute(self, context):
        rs_resolver.disconnect()
        tag_redraw()

        return {'FINISHED'}


class RESOLVER_OP_sync_scene(bpy.types.Operator):
    bl_idname = 'render_studio.sync_scene'
    bl_label = "Sync Scene"
    bl_description = "Sync scene to AMD RenderStudio"

    @classmethod
    def poll(cls, context):
        return rs_resolver.is_connected

    def execute(self, context):
        rs_resolver.sync_scene()
        tag_redraw()

        return {'FINISHED'}


class RESOLVER_OP_start_live_sync(bpy.types.Operator):
    bl_idname = 'render_studio.start_live_sync'
    bl_label = "Start Live Sync"
    bl_description = "Start live syncing: scene will be synced on every scene update"

    @classmethod
    def poll(cls, context):
        return rs_resolver.is_connected

    def execute(self, context):
        rs_resolver.start_live_sync()
        tag_redraw()

        return {'FINISHED'}


class RESOLVER_OP_stop_live_sync(bpy.types.Operator):
    bl_idname = 'render_studio.stop_live_sync'
    bl_label = "Stop Live Sync"
    bl_description = "Stop live syncing scene"

    @classmethod
    def poll(cls, context):
        return rs_resolver.is_connected

    def execute(self, context):
        rs_resolver.stop_live_sync()
        tag_redraw()

        return {'FINISHED'}


register_classes, unregister_classes = bpy.utils.register_classes_factory([
    RESOLVER_OP_connect,
    RESOLVER_OP_disconnect,
    RESOLVER_OP_sync_scene,
    RESOLVER_OP_start_live_sync,
    RESOLVER_OP_stop_live_sync,
])


def register():
    register_classes()


def unregister():
    unregister_classes()
