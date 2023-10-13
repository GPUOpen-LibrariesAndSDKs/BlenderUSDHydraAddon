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
from pathlib import Path
import sys
import os
import platform

from pxr import Plug

from . import engine, properties, ui, preferences


bl_info = {
    "name": "Hydra render engine: RPR",
    "author": "AMD",
    "version": (2, 0, 5),
    "blender": (4, 0, 0),
    "location": "Info header > Render engine menu",
    "description": "Radeon™ ProRender delegate for Hydra render engine",
    "tracker_url": "",
    "doc_url": "",
    "community": "",
    "downloads": "",
    "main_web": "",
    "category": "Render"
}

LIBS_DIR = Path(__file__).parent / "libs"


def register():
    if platform.system() == 'Windows':
        os.environ['PATH'] = os.environ['PATH'] + \
            os.pathsep + str(LIBS_DIR / "lib")

    sys.path.append(str(LIBS_DIR / "python"))
    Plug.Registry().RegisterPlugins(str(LIBS_DIR / "plugin"))

    preferences.register()
    engine.register()
    properties.register()
    ui.register()

    if platform.system() == 'Windows':
        from . import render_studio
        render_studio.register()


def unregister():
    if platform.system() == 'Windows':
        from . import render_studio
        render_studio.unregister()

    ui.unregister()
    properties.unregister()
    engine.unregister()
    preferences.unregister()
