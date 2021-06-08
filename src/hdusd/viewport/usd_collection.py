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

from ..utils import logging
log = logging.Log(tag='usd_collection')


COLLECTION_NAME = "USD NodeTree"


def update(context):
    clear(context)

    usd_tree_name = context.scene.hdusd.viewport.data_source
    if not usd_tree_name:
        return

    output_node = bpy.data.node_groups[usd_tree_name].get_output_node()
    if not output_node:
        return

    stage = output_node.cached_stage()
    if not stage:
        return

    create(context, stage)


def clear(context):
    collection = bpy.data.collections.get(COLLECTION_NAME)
    if not collection:
        return

    for obj in collection.objects:
        if obj.hdusd.is_usd:
            bpy.data.objects.remove(obj)

    bpy.data.collections.remove(collection)


def create(context, stage):
    collection = bpy.data.collections.get(COLLECTION_NAME)
    if not collection:
        collection = bpy.data.collections.new(COLLECTION_NAME)
        context.scene.collection.children.link(collection)
        log("Collection created", collection)

    def create_objects(root_obj, root_prim):
        for prim in root_prim.GetAllChildren():
            obj = bpy.data.objects.new('/', None)
            obj.hdusd.sync_from_prim(root_obj, prim)
            collection.objects.link(obj)

            create_objects(obj, prim)

    create_objects(None, stage.GetPseudoRoot())


def scene_save_pre():
    context = bpy.context
    clear(context)


def scene_save_post():
    context = bpy.context
    update(context)
