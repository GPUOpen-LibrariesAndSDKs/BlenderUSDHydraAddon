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

from .. import log
from . import base_node, categories
from . import (
    gen_standard_surface,
    gen_usd_preview_surface,
    gen_stdlib_defs,
    gen_pbrlib_defs
)


mx_nodedef_classes = [
    *gen_standard_surface.mx_nodedef_classes,
    *gen_usd_preview_surface.mx_nodedef_classes,
    *gen_stdlib_defs.mx_nodedef_classes,
    *gen_pbrlib_defs.mx_nodedef_classes,
]
mx_node_classes = [
    *gen_standard_surface.mx_node_classes,
    *gen_usd_preview_surface.mx_node_classes,
    *gen_stdlib_defs.mx_node_classes,
    *gen_pbrlib_defs.mx_node_classes,
]

register_sockets, unregister_sockets = bpy.utils.register_classes_factory([
    base_node.MxNodeInputSocket,
    base_node.MxNodeOutputSocket,
])
register_nodedefs, unregister_nodedefs = bpy.utils.register_classes_factory(mx_nodedef_classes)
register_nodes, unregister_nodes = bpy.utils.register_classes_factory(mx_node_classes)


def register():
    register_sockets()
    register_nodedefs()
    register_nodes()

    nodeitems_utils.register_node_categories("'HdUSD_MX_NODES", categories.get_node_categories())


def unregister():
    nodeitems_utils.unregister_node_categories("'HdUSD_MX_NODES")

    unregister_nodes()
    unregister_nodedefs()
    unregister_sockets()


def get_node_def_cls(node_name, nd_type):
    nd_name = f"ND_{node_name}_{nd_type}"
    node_def_cls = next((cls for cls in mx_nodedef_classes if cls.__name__.endswith(nd_name)), None)
    if node_def_cls:
        return node_def_cls

    nd_name = f"ND_{node_name}"
    return next(cls for cls in mx_nodedef_classes if cls.__name__.endswith(nd_name))


def get_mx_node_cls(node_name, nd_type):
    return next(cls for cls in mx_node_classes if cls.__name__.endswith(node_name) and
                nd_type in cls._data_types)
