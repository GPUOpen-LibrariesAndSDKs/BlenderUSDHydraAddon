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
from bpy.props import (
    PointerProperty,
    EnumProperty,
    BoolProperty,
)

from pxr import UsdImagingGL

from ..usd_nodes.node_tree import get_usd_nodetree
from . import log


render_delegates = []
for plugin_type_name in UsdImagingGL.Engine.GetRendererPlugins():
    display_name = UsdImagingGL.Engine.GetRendererDisplayName(plugin_type_name)
    render_delegates.append((plugin_type_name, display_name, display_name))

log("Registering Render Delegates", render_delegates)


class HdUSD_RenderDelegate(bpy.types.PropertyGroup):
    """ Settings for Render Delegate and their properties """

    # Render Delegate
    delegate: EnumProperty(
        name="Renderer",
        items=render_delegates,
        default='HdRprPlugin',
    )

    use_usd_nodegraph: BoolProperty(
        name="Use USD Nodegraph",
        default=True
    )    

    @property
    def is_opengl(self):
        return self.delegate == 'HdStormRendererPlugin'

    @property
    def is_usd_nodegraph(self):
        return self.use_usd_nodegraph and get_usd_nodetree() is not None

    @classmethod
    def register(cls):
        log("Register HdUSD_RenderProperties")
        bpy.types.Scene.hd_viewport = PointerProperty(
            name="HD viewport Settings",
            description="HD viewport Settings",
            type=cls,
        )

        bpy.types.Scene.hd_final = PointerProperty(
            name="HD final Settings",
            description="HD final Settings",
            type=cls,
        )

    @classmethod
    def unregister(cls):
        log("Unregister HdUSD_RenderProperties")
        del bpy.types.Scene.hd_viewport
        del bpy.types.Scene.hd_final
