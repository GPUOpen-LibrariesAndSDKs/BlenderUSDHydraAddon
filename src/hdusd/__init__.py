#**********************************************************************
# Copyright 2020 Advanced Micro Devices, Inc
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
#********************************************************************

bl_info = {
    "name": "USD Hydra",
    "author": "AMD",
    "version": (1, 1, 6),
    "blender": (2, 93, 0),
    "location": "Info header, render engine menu",
    "description": "USD Hydra rendering plugin for Blender",
    "warning": "",
    "tracker_url": "https://github.com/GPUOpen-LibrariesAndSDKs/BlenderUSDHydraAddon/issues",
    "doc_url": "https://radeon-pro.github.io/RadeonProRenderDocs/en/usd_hydra/about.html",
    "category": "Render",
    "community": "https://github.com/GPUOpen-LibrariesAndSDKs/BlenderUSDHydraAddon/discussions",
    "downloads": "https://github.com/GPUOpen-LibrariesAndSDKs/BlenderUSDHydraAddon/releases",
    "main_web": "https://www.amd.com/en/technologies/radeon-prorender",
}
version_build = ""


import tempfile
from pathlib import Path
from logging import getLevelName

from . import config
from .utils import logging, temp_dir

import bpy
from bpy.types import AddonPreferences
from bpy.props import StringProperty, BoolProperty, EnumProperty


class HDUSD_ADDON_PT_preferences(AddonPreferences):
    bl_idname = __name__

    def update_temp_dir(self, value):
        if not Path(self.tmp_dir).exists() or tempfile.gettempdir() == str(Path(self.tmp_dir)):
            log.info(f"Current temp directory is {tempfile.gettempdir()}")
            return

        tempfile.tempdir = Path(self.tmp_dir)
        bpy.context.preferences.addons[__name__].preferences['tmp_dir'] = str(temp_dir())
        log.info(f"Current temp directory is changed to {bpy.context.preferences.addons[__name__].preferences.tmp_dir}")

    def update_dev_tools(self, context):
        config.show_dev_settings = self.dev_tools
        log.info(f"Developer settings is {'enabled' if self.dev_tools else 'disabled'}")

    def update_log_level(self, context):
        logging.logger.setLevel(self.log_level)
        log.critical(f"Log level is set to {self.log_level}")

    tmp_dir: StringProperty(
        name="Temp Directory",
        description="Set temp directory",
        maxlen=1024,
        subtype='DIR_PATH',
        default=str(temp_dir()),
        update=update_temp_dir,
    )
    dev_tools: BoolProperty(
        name="Developer Tools",
        description="Enable developer tools",
        default=config.show_dev_settings,
        update=update_dev_tools,
    )
    log_level: EnumProperty(
        name="Log Level",
        description="Select logging level",
        items=(('DEBUG', "Debug", "Log level DEBUG"),
               ('INFO', "Info", "Log level INFO"),
               ('WARNING', "Warning", "Log level WARN"),
               ('ERROR', "Error", "Log level ERROR"),
               ('CRITICAL', "Critical", "Log level CRITICAL")),
        default=getLevelName(logging.logger.level),
        update=update_log_level,

    )
    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "tmp_dir", icon='NONE' if Path(self.tmp_dir).exists() else 'ERROR')
        col.prop(self, "dev_tools")
        col.prop(self, "log_level")
        col.separator()
        row = col.row()
        row.operator("wm.url_open", text="Main Site", icon='URL').url = bl_info["main_web"]
        row.operator("wm.url_open", text="Community", icon='COMMUNITY').url = bl_info["community"]
        row.operator("wm.url_open", text="Downloads", icon='TRIA_DOWN_BAR').url = bl_info["downloads"]


log = logging.Log('init')
log.info(f"Loading USD Hydra addon version={bl_info['version']}, build={version_build}")

from . import engine, properties, ui, usd_nodes, mx_nodes, bl_nodes


def register():
    """ Register all addon classes in Blender """
    log("register")

    engine.register()
    bl_nodes.register()
    mx_nodes.register()
    usd_nodes.register()
    properties.register()
    ui.register()
    bpy.utils.register_class(HDUSD_ADDON_PT_preferences)


def unregister():
    """ Unregister all addon classes from Blender """
    log("unregister")

    mx_nodes.unregister()
    usd_nodes.unregister()
    bl_nodes.unregister()
    ui.unregister()
    properties.unregister()
    engine.unregister()
    bpy.utils.unregister_class(HDUSD_ADDON_PT_preferences)
