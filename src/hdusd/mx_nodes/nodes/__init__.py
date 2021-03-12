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

from ...utils import HDUSD_LIBS_DIR
from .. import log
from . import base_node, categories


node_def_classes, mx_node_classes = base_node.create_node_types([
    ('PBR', HDUSD_LIBS_DIR / "materialx/libraries/bxdf/standard_surface.mtlx"),
    ('USD', HDUSD_LIBS_DIR / "materialx/libraries/bxdf/usd_preview_surface.mtlx"),
    ('STD', HDUSD_LIBS_DIR / "materialx/libraries/stdlib/stdlib_defs.mtlx"),
    ('PBR', HDUSD_LIBS_DIR / "materialx/libraries/pbrlib/pbrlib_defs.mtlx"),
])


register_sockets, unregister_sockets = bpy.utils.register_classes_factory([
    base_node.MxNodeInputSocket,
    base_node.MxNodeOutputSocket,
])
register_nodedefs, unregister_nodedefs = bpy.utils.register_classes_factory(node_def_classes)
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
    node_def_cls = next((cls for cls in node_def_classes if cls.mx_nodedef.getName() == nd_name),
                        None)
    if node_def_cls:
        return node_def_cls

    nd_name = f"ND_{node_name}"
    return next(cls for cls in node_def_classes if cls.mx_nodedef.getName() == nd_name)


def get_mx_node_cls(node_name, nd_type):
    nd_name = f"ND_{node_name}_{nd_type}"
    for cls in mx_node_classes:
        if next((nd for nd in cls.mx_nodedefs if nd.getName() == nd_name), None):
            return cls

    nd_name = f"ND_{node_name}"
    for cls in mx_node_classes:
        if next((nd for nd in cls.mx_nodedefs if nd.getName() == nd_name), None):
            return cls

    raise StopIteration(node_name, nd_type)
