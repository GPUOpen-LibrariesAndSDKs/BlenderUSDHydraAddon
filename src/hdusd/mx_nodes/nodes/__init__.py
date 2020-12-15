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
# from . import (
#     read_usd_file, read_blend_data, write_file, merge, print_file, filter, usd_to_blender,
#     hydra_render, rpr_render_settings
# )


from .base_node import create_node_types


node_types = create_node_types()


class MxNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'hdusd.MxNodeTree'


node_categories = [
    MxNodeCategory('HdUSD_MX_INPUT', "Input", items=[
        NodeItem('hdusd.MX_standard_surface'),
        NodeItem('usd.ReadUsdFileNode'),
    ]),
    # MxNodeCategory('HdUSD_OUTPUT', 'Output', items=[
    #     NodeItem('usd.HydraRenderNode'),
    #     NodeItem('usd.WriteFileNode'),
    #     NodeItem('usd.PrintFileNode'),
    # ]),
    # MxNodeCategory('HdUSD_CONVERTER', 'Converter', items=[
    #     NodeItem('usd.MergeNode'),
    #     # NodeItem('usd.FilterNode'),
    # ]),
]

# nodes to register
register_nodes, unregister_nodes = bpy.utils.register_classes_factory(node_types)


def register():
    register_nodes()
    nodeitems_utils.register_node_categories("MX_NODES", node_categories)


def unregister():
    nodeitems_utils.unregister_node_categories("MX_NODES")
    unregister_nodes()
