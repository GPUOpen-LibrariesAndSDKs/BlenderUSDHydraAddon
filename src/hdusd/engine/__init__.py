# **********************************************************************
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
# ********************************************************************
import os
import sys

import bpy

from .. import utils


if utils.IS_WIN:
    os.environ['PATH'] = f"{utils.HDUSD_LIBS_DIR / 'usd'};{utils.HDUSD_LIBS_DIR / 'plugins/usd'};" \
                         f"{utils.HDUSD_LIBS_DIR / 'hdrpr/lib'};{os.environ['PATH']}"

os.environ['PXR_PLUGINPATH_NAME'] = str(utils.HDUSD_LIBS_DIR / 'plugins')
os.environ['RPR'] = str(utils.HDUSD_LIBS_DIR / 'hdrpr')

sys.path.append(str(utils.HDUSD_LIBS_DIR / 'usd/python'))
sys.path.append(str(utils.HDUSD_LIBS_DIR / 'hdrpr/lib/python'))
sys.path.append(str(utils.HDUSD_LIBS_DIR / 'materialx/python'))

if utils.IS_WIN:
    # preload necessary dlls, required for python 3.9+
    import ctypes
    for lib_name in ["sdf", "usd", "usdGeom", "usdAppUtils", "glf", "usdImagingGL",
                     "usdImagingLite", "usdLux", "usdShade", "vt", "gf", "usdUtils"]:
        ctypes.CDLL(str(utils.HDUSD_LIBS_DIR / 'usd' / f"{lib_name}.dll"))


from . import engine, handlers


def register():
    bpy.utils.register_class(engine.HdUSDEngine)

    bpy.app.handlers.load_pre.append(handlers.on_load_pre)
    bpy.app.handlers.load_post.append(handlers.on_load_post)
    bpy.app.handlers.depsgraph_update_post.append(handlers.on_depsgraph_update_post)


def unregister():
    bpy.utils.unregister_class(engine.HdUSDEngine)

    bpy.app.handlers.load_pre.remove(handlers.on_load_pre)
    bpy.app.handlers.load_post.remove(handlers.on_load_post)
    bpy.app.handlers.depsgraph_update_post.remove(handlers.on_depsgraph_update_post)
