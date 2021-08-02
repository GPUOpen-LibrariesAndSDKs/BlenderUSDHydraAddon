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
import re

import bpy
from pxr import Usd, UsdGeom

from .base_node import USDNode


class RootNode(USDNode):
    """Takes in USD and filters out matching path or names"""
    bl_idname = 'usd.RootNode'
    bl_label = "Root"

    def update_data(self, context):
        self.reset()

    prefix_path: bpy.props.StringProperty(
        name="Prefix",
        description="USD Path pattern. Use special characters means:\n"
                    "  * - any word or subword\n"
                    "  ** - several words separated by '/' or subword",
        default='',
        update=update_data
    )

    prim_type:  bpy.props.EnumProperty(
        items=(('Xform', 'Xform', 'None'),
               ('None', 'None', 'Lossless texture compression')),
        default='Xform',
        name="Type",
        update = update_data
    )

    def draw_buttons(self, context, layout):
        layout.prop(self, 'prefix_path')
        layout.prop(self, 'prim_type')

    def compute(self, **kwargs):
        input_stage = self.get_input_link('Input', **kwargs)
        if not input_stage:
            return None


        def get_child_prims(prim):
            if not prim.IsPseudoRoot():
                yield prim
                return

            for child in prim.GetAllChildren():
                yield from get_child_prims(child)

        prims = tuple(get_child_prims(input_stage.GetPseudoRoot()))
        if not prims:
            return None

        stage = self.cached_stage.create()
        UsdGeom.SetStageMetersPerUnit(stage, 1)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)

        root_prim = stage.GetPseudoRoot()

        for i, prim in enumerate(prims, 1):
            override_prim = stage.OverridePrim(root_prim.GetPath().AppendChild(prim.GetName()))
            override_prim.GetReferences().AddReference(input_stage.GetRootLayer().realPath,
                                                       prim.GetPath())

        return stage
