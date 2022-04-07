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
    "version": (1, 0, 90),
    "blender": (2, 93, 0),
    "location": "Info header, render engine menu",
    "description": "USD Hydra rendering plugin for Blender",
    "warning": "",
    "tracker_url": "",
    "doc_url": "",
    "category": "Render"
}
version_build = ""


from . import config
from .utils import logging

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


def unregister():
    """ Unregister all addon classes from Blender """
    log("unregister")

    mx_nodes.unregister()
    usd_nodes.unregister()
    bl_nodes.unregister()
    ui.unregister()
    properties.unregister()
    engine.unregister()
