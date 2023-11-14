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
import platform
from pathlib import Path

import bpy

from . import logging


DEFAULT_RS_DIR = Path("C:/" if platform.system() == 'Windows' else "/var/lib") / "AMD/AMD RenderStudio"


class RPR_HYDRA_ADDON_PT_preferences(bpy.types.AddonPreferences):
    bl_idname = "hydrarpr"

    def rs_enable_update(self, context):
        from . import render_studio
        if self.rs_enable:
            render_studio.register()
        else:
            render_studio.unregister()

    def log_level_update(self, context):
        logging.logger.setLevel(self.log_level)

    log_level: bpy.props.EnumProperty(
        name="Log Level",
        description="Level of logging",
        items=(('DEBUG', "Debug", "Log level: Debug"),
               ('INFO', "Info", "Log level: Info"),
               ('WARN', "Warning", "Log level: Warning"),
               ('ERROR', "Error", "Log level: Error")),
        default=logging.DEFAULT_LEVEL,
        update=log_level_update,
    )
    rs_enable: bpy.props.BoolProperty(
        name="AMD RenderStudio",
        description="Enable AMD RenderStudio",
        default=False,
        update=rs_enable_update,
    )
    rs_workspace_dir: bpy.props.StringProperty(
        name="Workspace Dir",
        description="Set directory which would be synchronized for all connected users",
        subtype='DIR_PATH',
        default=str(DEFAULT_RS_DIR / "Workspace"),
    )
    rs_workspace_url: bpy.props.StringProperty(
        name="Workspace Url",
        description="Set URL of the remote server",
        default="",
    )
    rs_file_format: bpy.props.EnumProperty(
        name="USD File Format",
        description="File format of syncing USD file",
        items=(('.usd', "usd", "Either of the usda or usdc"),
               ('.usda', "usda", "Human-readable UTF-8 text"),
               ('.usdc', "usdc", "Random-access \"Crate\" binary")),
        default='.usd',
    )

    def draw(self, context):
        layout = self.layout

        layout.prop(self, "log_level")

        if platform.system() != 'Windows':
            return

        box = layout.box()
        row = box.row(align=True)
        row.prop(self, "rs_enable")
        if self.rs_enable:
            col = box.column(align=True)
            col.prop(self, "rs_workspace_url")
            # col.prop(self, "rs_workspace_dir")
            col.prop(self, "rs_file_format")


def preferences():
    return bpy.context.preferences.addons["hydrarpr"].preferences


register, unregister = bpy.utils.register_classes_factory((RPR_HYDRA_ADDON_PT_preferences,))
