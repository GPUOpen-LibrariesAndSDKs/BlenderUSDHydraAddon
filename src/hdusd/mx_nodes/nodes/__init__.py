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


nodedef_types, node_types = base_node.create_node_types([
    HDUSD_LIBS_DIR / "materialx/libraries/bxdf/standard_surface.mtlx",
    HDUSD_LIBS_DIR / "materialx/libraries/stdlib/stdlib_defs.mtlx",
    HDUSD_LIBS_DIR / "materialx/libraries/pbrlib/pbrlib_defs.mtlx",
])


register_sockets, unregister_sockets = bpy.utils.register_classes_factory([
    base_node.MxNodeInputSocket,
    base_node.MxNodeOutputSocket,
])
register_nodedefs, unregister_nodedefs = bpy.utils.register_classes_factory(nodedef_types)
register_nodes, unregister_nodes = bpy.utils.register_classes_factory([
    *node_types,
    base_node.MxNode_Output
])


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
