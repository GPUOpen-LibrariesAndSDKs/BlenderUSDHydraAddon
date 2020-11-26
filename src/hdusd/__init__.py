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
    "version": (1, 0, 0),
    "blender": (2, 90, 1),
    "location": "Info header, render engine menu",
    "description": "USD Hydra rendering plugin for Blender",
    "warning": "",
    "tracker_url": "",
    "wiki_url": "",
    "category": "Render"
}
version_build = ""


from . import config
from .utils import logging


log = logging.Log(tag='init')
log.info("Loading USD Hydra addon {}".format(bl_info['version']))


from . import engine, properties, ui, usd_nodes


def register():
    """ Register all addon classes in Blender """
    log("register")

    engine.register()
    properties.register()
    ui.register()
    usd_nodes.register()


def unregister():
    """ Unregister all addon classes from Blender """
    log("unregister")

    usd_nodes.unregister()
    ui.unregister()
    properties.unregister()
    engine.unregister()
