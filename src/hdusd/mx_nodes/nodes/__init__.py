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
import importlib
from pathlib import Path

import bpy
import nodeitems_utils

from .. import log
from . import base_node, categories

gen_modules = [importlib.import_module(f"hdusd.mx_nodes.nodes.{f.name[:-len(f.suffix)]}")
               for f in Path(__file__).parent.glob("gen_*.py")]

mx_node_classes = []
for m in gen_modules:
    mx_node_classes.extend(m.mx_node_classes)

register_sockets, unregister_sockets = bpy.utils.register_classes_factory([
    base_node.MxNodeInputSocket,
    base_node.MxNodeOutputSocket,
])
register_nodes, unregister_nodes = bpy.utils.register_classes_factory(mx_node_classes)


def register():
    register_sockets()
    register_nodes()

    nodeitems_utils.register_node_categories("'HdUSD_MX_NODES", categories.get_node_categories())


def unregister():
    nodeitems_utils.unregister_node_categories("'HdUSD_MX_NODES")

    unregister_nodes()
    unregister_sockets()


def get_mx_node_cls(node_name, nd_type):
    node_cls = next((cls for cls in mx_node_classes if cls.__name__.endswith(node_name) and
                nd_type in cls._data_types),
                None)
    if node_cls:
        return node_cls

    raise KeyError("Unable to find MaterialX node class", node_name, nd_type)
