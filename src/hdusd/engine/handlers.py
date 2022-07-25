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

from ..properties.scene import DEFAULT_DELEGATE
from .. import utils
from .engine import log


@bpy.app.handlers.persistent
def on_load_pre(*args):
    """Handler on loading a blend file (before)"""
    log("on_load_pre", args)
    utils.clear_temp_dir()


@bpy.app.handlers.persistent
def on_load_post(*args):
    """Handler on loading a blend file (after)"""
    log("on_load_post", args)
    from ..usd_nodes import node_tree
    node_tree.reset()

    for scene in bpy.data.scenes:
        if not scene.hdusd.final.delegate:
            scene.hdusd.final.delegate = DEFAULT_DELEGATE

        if not scene.hdusd.viewport.delegate:
            scene.hdusd.viewport.delegate = DEFAULT_DELEGATE

_do_depsgraph_update = True


@bpy.app.handlers.persistent
def on_depsgraph_update_post(scene, depsgraph):
    global _do_depsgraph_update
    if not _do_depsgraph_update:
        return

    log("on_depsgraph_update", depsgraph)
    from ..properties import object, material
    from ..usd_nodes import node_tree
    from ..ui import material as material_ui

    object.depsgraph_update(depsgraph)
    material.depsgraph_update(depsgraph)
    node_tree.depsgraph_update(depsgraph)
    material_ui.depsgraph_update(depsgraph)


def no_depsgraph_update_call(op, *args, **kwargs):
    """This function prevents call of self.update() during calling our function"""
    global _do_depsgraph_update
    if not _do_depsgraph_update:
        return op(*args, **kwargs)

    _do_depsgraph_update = False
    try:
        return op(*args, **kwargs)
    finally:
        _do_depsgraph_update = True


@bpy.app.handlers.persistent
def on_frame_change_post(scene, depsgraph):
    """Handler on frame change a blend file (after)"""
    log("on_frame_change", depsgraph)
    from ..usd_nodes import node_tree

    node_tree.frame_change(depsgraph)


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
