#**********************************************************************
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
#********************************************************************
import bpy
from pxr import UsdImagingGL

from ..usd_nodes.node_tree import get_usd_nodetree
from . import HdUSDProperties, usd_tree, log


_render_delegates = {name: UsdImagingGL.Engine.GetRendererDisplayName(name)
                     for name in UsdImagingGL.Engine.GetRendererPlugins()}
log("Render Delegates", _render_delegates)


class RenderDelegate(bpy.types.PropertyGroup):
    delegate: bpy.props.EnumProperty(
        name="Renderer",
        items=((name, display_name, f"Hydra render delegate: {display_name}")
               for name, display_name in _render_delegates.items()),
        default='HdRprPlugin',
    )
    use_usd_nodegraph: bpy.props.BoolProperty(
        name="Use USD Nodegraph",
        default=True
    )    

    @property
    def is_opengl(self):
        return self.delegate == 'HdStormRendererPlugin'

    @property
    def is_usd_nodegraph(self):
        return self.use_usd_nodegraph and get_usd_nodetree() is not None


class SceneProperties(HdUSDProperties):
    bl_type = bpy.types.Scene

    final: bpy.props.PointerProperty(type=RenderDelegate)
    viewport: bpy.props.PointerProperty(type=RenderDelegate)

    myNodes: bpy.props.CollectionProperty(type=usd_tree.MyListTreeNode)
    usd_tree: bpy.props.CollectionProperty(type=usd_tree.UsdTreeItem)
    usd_tree_index: bpy.props.IntProperty()
