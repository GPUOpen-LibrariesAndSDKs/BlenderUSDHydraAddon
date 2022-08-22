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
    path_str = ""
    for loc_path in ('lib', 'bin', 'plugin/usd'):
        path = utils.LIBS_DIR / loc_path
        os.add_dll_directory(str(path))
        path_str += f"{path};"

    os.environ['PATH'] = path_str + os.environ['PATH']

os.environ['PXR_PLUGINPATH_NAME'] = str(utils.LIBS_DIR / 'plugin')
os.environ['RPR'] = str(utils.LIBS_DIR)
os.environ['PXR_MTLX_STDLIB_SEARCH_PATHS'] = str(utils.LIBS_DIR / "libraries")

# internal scene index representation in hydra,
# see https://github.com/PixarAnimationStudios/USD/blob/release/CHANGELOG.md#imaging
os.environ["HD_ENABLE_SCENE_INDEX_EMULATION"] = "0"

sys.path.append(str(utils.LIBS_DIR / 'lib/python'))
sys.path.append(str(utils.LIBS_DIR / 'python'))


from . import engine, handlers


def register():
    bpy.utils.register_class(engine.HdUSDEngine)

    bpy.app.handlers.load_pre.append(handlers.on_load_pre)
    bpy.app.handlers.load_post.append(handlers.on_load_post)
    bpy.app.handlers.depsgraph_update_post.append(handlers.on_depsgraph_update_post)
    bpy.app.handlers.frame_change_post.append(handlers.on_frame_change_post)
    bpy.app.handlers.save_pre.append(handlers.on_save_pre)
    bpy.app.handlers.save_post.append(handlers.on_save_post)


def unregister():
    bpy.utils.unregister_class(engine.HdUSDEngine)

    bpy.app.handlers.load_pre.remove(handlers.on_load_pre)
    bpy.app.handlers.load_post.remove(handlers.on_load_post)
    bpy.app.handlers.depsgraph_update_post.remove(handlers.on_depsgraph_update_post)
    bpy.app.handlers.frame_change_post.remove(handlers.on_frame_change_post)
    bpy.app.handlers.save_pre.remove(handlers.on_save_pre)
    bpy.app.handlers.save_post.remove(handlers.on_save_post)
