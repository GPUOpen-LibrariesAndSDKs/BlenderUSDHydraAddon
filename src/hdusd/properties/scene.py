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
from ..viewport import usd_collection
from . import HdUSDProperties, log


_render_delegates = {name: UsdImagingGL.Engine.GetRendererDisplayName(name)
                     for name in UsdImagingGL.Engine.GetRendererPlugins()}
log("Render Delegates", _render_delegates)


class RenderSettings(bpy.types.PropertyGroup):
    def data_source_update(self, context):
        usd_collection.update(self.data_source)

    delegate: bpy.props.EnumProperty(
        name="Renderer",
        items=((name, display_name, f"Hydra render delegate: {display_name}")
               for name, display_name in _render_delegates.items()),
        default='HdRprPlugin',
    )
    data_source: bpy.props.StringProperty(
        name="Data Source",
        default="",
        update=data_source_update
    )

    @property
    def is_gl_delegate(self):
        return self.delegate == 'HdStormRendererPlugin'

    @property
    def is_usd_nodegraph(self):
        return self.use_usd_nodegraph and get_usd_nodetree() is not None


class SceneProperties(HdUSDProperties):
    bl_type = bpy.types.Scene

    final: bpy.props.PointerProperty(type=RenderSettings)
    viewport: bpy.props.PointerProperty(type=RenderSettings)

    rpr_viewport_cpu_device: bpy.props.BoolProperty(
        name="CPU Viewport Render Device",
        description="Use CPU device for viewport render in RPR.\n"
                    "Required for MaterialX testing when GPU isn't supported",
        default=False,
    )
    use_rpr_mx_nodes: bpy.props.BoolProperty(
        name="RPR MaterialX Nodes",
        description="Use RPR MaterialX Nodes as default nodes",
        default=True,
    )
