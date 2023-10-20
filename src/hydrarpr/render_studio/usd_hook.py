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

from .. import logging
log = logging.Log("rs.usd_hook")


class USDHookWorld(bpy.types.USDHook):
    bl_idname = "usd_hook_world"
    bl_label = "USD Hook World"
    bl_description = "Exports world to USD stage"

    @staticmethod
    def on_export(export_context):
        stage = export_context.get_stage()
        depsgraph = export_context.get_depsgraph()
        if not stage or not depsgraph.scene.world:
            return False

        from . import world
        try:
            world.sync(stage, depsgraph.scene.world)

        except Exception as err:
            log.warn("Can't sync world", err)
            return False

        return True


def register():
    bpy.utils.register_class(USDHookWorld)


def unregister():
    bpy.utils.unregister_class(USDHookWorld)
