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
import bpy

from .. import utils
from .engine import log


@bpy.app.handlers.persistent
def on_load_pre(*args):
    """ Handler on loading a blend file (before) """
    log("on_load_pre", args)
    utils.clear_temp_dir()


@bpy.app.handlers.persistent
def on_load_post(*args):
    """ Handler on loading a blend file (after) """
    log("on_load_post", args)
    from ..usd_nodes import node_tree
    node_tree.reset()

    from ..properties.usd_list import get_blender_prim_object
    get_blender_prim_object(bpy.context)


@bpy.app.handlers.persistent
def on_depsgraph_update_post(scene, depsgraph):
    from ..properties import usd_list
    from ..usd_nodes import node_tree

    usd_list.depsgraph_update(depsgraph)
    node_tree.depsgraph_update(depsgraph)


@bpy.app.handlers.persistent
def on_save_pre(*args):
    log("on_save_pre", args)
    from ..viewport import usd_collection
    usd_collection.scene_save_pre()


@bpy.app.handlers.persistent
def on_save_post(*args):
    log("on_save_post", args)
    from ..viewport import usd_collection
    usd_collection.scene_save_post()
