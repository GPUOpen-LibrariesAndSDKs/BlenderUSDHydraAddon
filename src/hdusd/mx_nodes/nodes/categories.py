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
from collections import defaultdict

from nodeitems_utils import NodeCategory, NodeItem

from ...utils import prettify_string
from .base_node import MxNode_Output


class MxNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'hdusd.MxNodeTree'


def get_node_categories():
    from . import node_types

    d = defaultdict(list)
    for n_type in node_types:
        nodegroup = n_type.mx_nodedefs[0].getAttribute('nodegroup')
        d[nodegroup].append(n_type)

    categories = []
    for nodegroup, n_types in d.items():
        categories.append(
            MxNodeCategory('HdUSD_MX_NG_' + nodegroup, prettify_string(nodegroup),
                           items=[NodeItem(n_type.bl_idname) for n_type in n_types]))

    categories.append(
        MxNodeCategory('HdUSD_MX_NG_output', "Output", items=[NodeItem(MxNode_Output.bl_idname)]))
    return categories
