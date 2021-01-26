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

from ...utils import title_str


class MxNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return context.space_data.tree_type == 'hdusd.MxNodeTree'


def get_node_categories():
    from . import mx_node_classes

    d = defaultdict(list)
    for MxNode_cls in mx_node_classes:
        nodegroup = MxNode_cls.mx_nodedefs[0].getAttribute('nodegroup')
        d[nodegroup].append(MxNode_cls)

    categories = []
    for nodegroup,  cat_classes in d.items():
        categories.append(
            MxNodeCategory('HdUSD_MX_NG_' + nodegroup, title_str(nodegroup),
                           items=[NodeItem(MxNode_cls.bl_idname) for MxNode_cls in cat_classes]))

    return categories
