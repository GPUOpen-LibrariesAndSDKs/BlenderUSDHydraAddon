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
for mod in gen_modules:
    mx_node_classes.extend(mod.mx_node_classes)

# sorting by category and label
mx_node_classes = sorted(mx_node_classes, key=lambda cls: (cls.category.lower(), cls.bl_label.lower()))


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


def get_mx_node_cls(mx_node):
    node_name = mx_node.getCategory()

    suffix = f'_{node_name}'
    classes = tuple(cls for cls in mx_node_classes if cls.__name__.endswith(suffix))
    if not classes:
        raise KeyError(f"Unable to find MxNode class for {mx_node}")

    def params_set(node, out_type):
        return {f"in_{p.getName()}:{p.getType()}" for p in node.getActiveInputs()} | \
               {out_type}

    node_params_set = params_set(mx_node, mx_node.getType())

    for cls in classes:
        for nodedef, data_type in cls.get_nodedefs():
            nd_outputs = nodedef.getActiveOutputs()
            nd_params_set = params_set(nodedef, 'multioutput' if len(nd_outputs) > 1 else
                                       nd_outputs[0].getType())
            if node_params_set.issubset(nd_params_set):
                return cls, data_type

    raise TypeError(f"Unable to find suitable nodedef for {mx_node}")
