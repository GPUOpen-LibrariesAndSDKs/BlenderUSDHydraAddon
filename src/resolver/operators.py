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


class RESOLVER_OP_connect(bpy.types.Operator):
    bl_idname = 'resolver.connect'
    bl_label = "Connect"
    bl_description = "Connect to Render Studio Resolver server"

    def execute(self, context):
        from .resolver import rs_resolver
        rs_resolver.connect()
        rs_resolver.open_usd()

        return {'FINISHED'}


class RESOLVER_OP_disconnect(bpy.types.Operator):
    bl_idname = 'resolver.disconnect'
    bl_label = "Disconnect"
    bl_description = "Disconnect Render Studio Resolver server"

    def execute(self, context):
        from .resolver import rs_resolver
        rs_resolver.disconnect()
        return {'FINISHED'}


class RESOLVER_OP_export_stage_to_string(bpy.types.Operator):
    bl_idname = 'resolver.export_stage'
    bl_label = "Export Stage to Console"
    bl_description = "Export current USD stage to console"

    def execute(self, context):
        from .resolver import rs_resolver
        print(rs_resolver.stage.ExportToString())
        return {'FINISHED'}


register_classes, unregister_classes = bpy.utils.register_classes_factory([
    RESOLVER_OP_connect,
    RESOLVER_OP_disconnect,
    RESOLVER_OP_export_stage_to_string,
    ])

def register():
    register_classes()


def unregister():
    unregister_classes()
