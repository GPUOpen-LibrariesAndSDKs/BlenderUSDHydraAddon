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
import bpy

from pxr import Sdf

from ..engine import handlers
from ..utils import usd as usd_utils
from ..properties.object import GEOM_TYPES

from ..utils import logging
log = logging.Log('usd_collection')


COLLECTION_NAME = "USD NodeTree"


def ignore_prim(prim):
    prim_type = prim.GetTypeName()
    if not prim_type:
        return False

    return not (prim_type in GEOM_TYPES or prim_type in ('Mesh', 'Camera') or prim_type.endswith('Light'))


def update(context):
    def update_():
        usd_tree_name = context.scene.hdusd.viewport.data_source
        if not usd_tree_name:
            clear(context)
            return

        output_node = bpy.data.node_groups[usd_tree_name].get_output_node()
        if not output_node:
            clear(context)
            return

        stage = output_node.cached_stage()
        if not stage:
            clear(context)
            return

        # workaround for Undo operation - Blender doesn't send bpy.data.scenes and bpy.data.collections
        # so we need to do nothing to prevent Blender crash
        if len(bpy.data.scenes) == 0:
            return

        collection = bpy.data.collections.get(COLLECTION_NAME)
        if not collection:
            collection = bpy.data.collections.new(COLLECTION_NAME)
            context.scene.collection.children.link(collection)
            log("Collection created", collection)

        objects = {}
        for obj in collection.objects:
            if obj.hdusd.is_usd:
                objects[obj.hdusd.sdf_path] = obj
        obj_paths = set(objects.keys())

        prim_paths = set()
        for prim in usd_utils.traverse_stage(stage, ignore=ignore_prim):
            prim_paths.add(str(prim.GetPath()))

        paths_to_remove = obj_paths - prim_paths
        paths_to_add = prim_paths - obj_paths
        path_to_update = obj_paths.intersection(prim_paths)

        log(f"Removing {len(paths_to_remove)} objects")
        for path in paths_to_remove:
            obj = objects.pop(path)
            bpy.data.objects.remove(obj)

        log(f"Updated {len(path_to_update)} objects")
        for path in path_to_update:
            prim = stage.GetPrimAtPath(path)
            if prim.GetTypeName() in GEOM_TYPES:
                objects[path].hdusd.sync_transform_from_prim(prim)

        log(f"Adding {len(paths_to_add)} objects")
        for path in sorted(paths_to_add):
            parent_path = str(Sdf.Path(path).GetParentPath())
            parent_obj = None if parent_path == '/' else objects[parent_path]

            prim = stage.GetPrimAtPath(path)
            obj = bpy.data.objects.new('/', None)
            obj.hdusd.sync_from_prim(parent_obj, prim)
            collection.objects.link(obj)

            objects[path] = obj

    handlers.no_depsgraph_update_call(update_)

def clear(context):
    def clear_():
        collection = bpy.data.collections.get(COLLECTION_NAME)
        if not collection:
            return

        log("Removing collection", collection)
        for obj in collection.objects:
            if obj.hdusd.is_usd:
                bpy.data.objects.remove(obj)

        bpy.data.collections.remove(collection)

    handlers.no_depsgraph_update_call(clear_)


def scene_save_pre():
    context = bpy.context
    clear(context)


def scene_save_post():
    context = bpy.context
    update(context)
