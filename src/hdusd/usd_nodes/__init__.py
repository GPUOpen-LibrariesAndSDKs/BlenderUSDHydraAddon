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
from ..utils import logging
log = logging.Log("usd_nodes")

import bpy

from . import node_tree
from . import nodes


register_trees, unregister_trees = bpy.utils.register_classes_factory([
    node_tree.USDTree,
    # node_tree.RenderTaskTree,
])


def register():
    register_trees()
    nodes.register()


def unregister():
    unregister_trees()
    nodes.unregister()
