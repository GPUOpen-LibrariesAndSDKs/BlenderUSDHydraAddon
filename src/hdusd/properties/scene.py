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
import os
from pxr import UsdImagingGL

from ..viewport import usd_collection
from . import HdUSDProperties, hdrpr_render, log


_render_delegates = {name: UsdImagingGL.Engine.GetRendererDisplayName(name)
                     for name in UsdImagingGL.Engine.GetRendererPlugins()}

if not os.path.isdir(os.environ.get('RMANTREE', "")):
    _render_delegates.pop('HdPrmanLoaderRendererPlugin', None)

log("Render Delegates", _render_delegates)


class RenderSettings(bpy.types.PropertyGroup):
    delegate_items = tuple((name, display_name, f"Hydra render delegate: {display_name}")
                           for name, display_name in _render_delegates.items())

    @property
    def is_gl_delegate(self):
        return self.delegate == 'HdStormRendererPlugin'

    @property
    def delegate_name(self):
        return _render_delegates[self.delegate]

    hdrpr: bpy.props.PointerProperty(type=hdrpr_render.RenderSettings)


class FinalRenderSettings(RenderSettings):
    delegate: bpy.props.EnumProperty(
        name="Renderer",
        items=RenderSettings.delegate_items,
        description="Render delegate for final render",
        default='HdRprPlugin',
    )
    data_source: bpy.props.StringProperty(
        name="Data Source",
        description="Data source for final render",
        default=""
    )
    nodetree_camera: bpy.props.StringProperty(
        name="Camera",
        description="Select camera from USD for final render",
        default=""
    )

    def nodetree_update(self, context):
        if not self.data_source:
            self.nodetree_camera = ""
            return

        output_node = bpy.data.node_groups[self.data_source].get_output_node()
        if not output_node:
            self.nodetree_camera = ""
            return

        stage = output_node.cached_stage()
        if not stage:
            self.nodetree_camera = ""
            return

        if self.nodetree_camera:
            prim = stage.GetPrimAtPath(self.nodetree_camera)
            if prim and prim.GetTypeName() == "Camera":
                return

        self.nodetree_camera = ""
        for prim in stage.TraverseAll():
            if prim.GetTypeName() == "Camera":
                self.nodetree_camera = prim.GetPath().pathString
                break


class ViewportRenderSettings(RenderSettings):
    delegate: bpy.props.EnumProperty(
        name="Renderer",
        items=RenderSettings.delegate_items,
        default='HdRprPlugin',
    )

    def data_source_update(self, context):
        usd_collection.update(context)

    data_source: bpy.props.StringProperty(
        name="Data Source",
        description="Data source for viewport render",
        default="",
        update=data_source_update
    )


class SceneProperties(HdUSDProperties):
    bl_type = bpy.types.Scene

    final: bpy.props.PointerProperty(type=FinalRenderSettings)
    viewport: bpy.props.PointerProperty(type=ViewportRenderSettings)
