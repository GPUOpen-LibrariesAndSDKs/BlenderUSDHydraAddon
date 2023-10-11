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

bl_info = {
    "name": "Render Studio Resolver",
    "author": "AMD",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "Info header > Render engine menu",
    "description": "Radeon Render Studio Resolver for Hydra render engine",
    "tracker_url": "",
    "doc_url": "",
    "community": "",
    "downloads": "",
    "main_web": "",
    "support": 'TESTING',
    "category": "Render"
}

import os
import sys
import platform
from pathlib import Path
import bpy
from pxr import Plug


LIBS_DIR = Path(__file__).parent / "libs"


def preload_resolver():
    root_folder = "blender.shared" if platform.system() == 'Windows' else "lib"
    path = os.pathsep.join([str(Path(bpy.app.binary_path).parent / f"{root_folder}")])
    os.add_dll_directory(path)
    os.add_dll_directory(str(LIBS_DIR / "lib"))
    os.environ['PATH'] += ";" + str(LIBS_DIR / "lib")
    sys.path.append(str(LIBS_DIR / "python"))
    Plug.Registry().RegisterPlugins(str(LIBS_DIR / "plugin"))
    usd_plugin = Plug.Registry().GetPluginWithName('RenderStudioResolver')
    if not usd_plugin.isLoaded:
        usd_plugin.Load()


from . import ui, operators


def register():
    preload_resolver()
    operators.register()
    ui.register()

    from .resolver import rs_resolver
    bpy.app.handlers.depsgraph_update_post.append(rs_resolver.on_depsgraph_update_post)


def unregister():
    from .resolver import rs_resolver
    rs_resolver.disconnect()

    if rs_resolver.on_depsgraph_update_post in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(rs_resolver.on_depsgraph_update_post)

    ui.unregister()
    operators.unregister()
