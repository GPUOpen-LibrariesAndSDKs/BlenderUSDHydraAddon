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
        if not stage:
            return False

        from . import world
        settings = bpy.context.scene.hydra_rpr.render_studio
        try:
            if settings.export_world:
                world.sync(stage, export_context.get_depsgraph())

        except Exception as err:
            log.warn("Can't sync world", err)
            return False

        return True


def register():
    if not USDHookWorld.is_registered:
        bpy.utils.register_class(USDHookWorld)

    log(f"{USDHookWorld.__name__} is enabled")


def unregister():
    if USDHookWorld.is_registered:
        bpy.utils.unregister_class(USDHookWorld)

    log(f"{USDHookWorld.__name__} is disabled")
