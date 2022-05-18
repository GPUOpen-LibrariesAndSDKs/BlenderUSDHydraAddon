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
import nodeitems_utils
from nodeitems_utils import NodeCategory, NodeItem
from .. import log

# classes to register
from . import (
    usd_file, blender_data, write_file, merge, print_file, filter, root, instancing, usd_to_blender,
    hydra_render, rpr_render_settings, transformations
)


class USDNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'hdusd.USDTree'


node_categories = [
    USDNodeCategory('HdUSD_USD_INPUT', "Input", items=[
        NodeItem('usd.BlenderDataNode'),
        NodeItem('usd.UsdFileNode'),
    ]),
    USDNodeCategory('HdUSD_USD_OUTPUT', 'Output', items=[
        NodeItem('usd.HydraRenderNode'),
        NodeItem('usd.WriteFileNode'),
        # NodeItem('usd.PrintFileNode'),
    ]),
    USDNodeCategory('HdUSD_USD_CONVERTER', 'Converter', items=[
        NodeItem('usd.MergeNode'),
        NodeItem('usd.FilterNode'),
        NodeItem('usd.IgnoreNode'),
        NodeItem('usd.RootNode'),
        NodeItem('usd.InstancingNode'),
    ]),
    USDNodeCategory('HdUSD_USD_TRANSFORMATIONS', 'Transformations', items=[
        NodeItem('usd.TransformNode'),
        NodeItem('usd.TransformByEmptyNode'),
    ]),
    USDNodeCategory('HdUSD_USD_LAYOUT', 'Layout', items=[
        NodeItem('NodeFrame'),
        NodeItem('NodeReroute'),
    ]),
]

# nodes to register
register_classes, unregister_classes = bpy.utils.register_classes_factory([
    blender_data.HDUSD_USD_NODETREE_OP_blender_data_link_collection,
    blender_data.HDUSD_USD_NODETREE_OP_blender_data_unlink_collection,
    blender_data.HDUSD_USD_NODETREE_MT_blender_data_collection,
    blender_data.HDUSD_USD_NODETREE_OP_blender_data_link_object,
    blender_data.HDUSD_USD_NODETREE_OP_blender_data_unlink_object,
    blender_data.HDUSD_USD_NODETREE_MT_blender_data_object,
    blender_data.BlenderDataNode,
    instancing.HDUSD_USD_NODETREE_MT_instancing_object,

    usd_file.UsdFileNode,
    write_file.WriteFileNode,
    merge.MergeNode,
    # print_file.PrintFileNode,
    filter.FilterNode,
    filter.IgnoreNode,
    root.RootNode,
    instancing.InstancingNode,
    usd_to_blender.USDToBlenderNode,
    hydra_render.HydraRenderNode,
    rpr_render_settings.RprRenderSettingsNode,
    transformations.HDUSD_USD_NODETREE_OP_transform_add_empty,
    transformations.TransformNode,
    transformations.TransformByEmptyNode,
])


def register():
    register_classes()
    nodeitems_utils.register_node_categories("USD_NODES", node_categories)


def unregister():
    nodeitems_utils.unregister_node_categories("USD_NODES")
    unregister_classes()
