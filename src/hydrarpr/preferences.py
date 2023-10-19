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
import uuid
import os
from pathlib import Path

import bpy


RS_SERVER_URL = ""
RS_STORAGE_URL = ""
RS_STORAGE_DIR = Path(os.path.expandvars('%appdata%')) / "AMD RenderStudio"

try:
    from . import configdev
except ImportError:
    pass


def rs_enable(self, context):
    from . import render_studio
    if self.rs_enable:
        render_studio.register()

    else:
        render_studio.unregister()


class RPR_HYDRA_ADDON_PT_preferences(bpy.types.AddonPreferences):
    bl_idname = "hydrarpr"

    rs_enable: bpy.props.BoolProperty(
        name="AMD RenderStudio",
        description="Enable AMD RenderStudio",
        default=False,
        update=rs_enable,
    )
    rs_server_url: bpy.props.StringProperty(
        name="Server Address",
        description="Set address of remote live server",
        default=RS_SERVER_URL,
    )
    rs_storage_url: bpy.props.StringProperty(
        name="Storage Address",
        description="Set address of remote assets storage",
        default=RS_STORAGE_URL,
    )
    rs_storage_dir: bpy.props.StringProperty(
        name="Storage Dir",
        description="Set directory which would be synchronized for all connected users",
        subtype='DIR_PATH',
        default=str(RS_STORAGE_DIR),
    )
    rs_file_format: bpy.props.EnumProperty(
        name="Usd File Format",
        items=(('USD', "usd", "Either of the usda or usdc"),
               ('USDA', "usda", "Human-readable UTF-8 text"),
               ('USDC', "usdc", "Random-access “Crate” binary")),
        default='USD',
    )

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        row = box.row(align=True)
        row.prop(self, "rs_enable")
        if self.rs_enable:
            col = box.column(align=True)
            # col.prop(self, "rs_server_url", icon='NONE')
            col.prop(self, "rs_storage_dir")
            col.prop(self, "rs_file_format")


def preferences():
    return bpy.context.preferences.addons["hydrarpr"].preferences


register, unregister = bpy.utils.register_classes_factory((RPR_HYDRA_ADDON_PT_preferences,))
