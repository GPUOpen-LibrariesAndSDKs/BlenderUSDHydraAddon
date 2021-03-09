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
from .base_node import USDNode
from . import log


class FilterNode(USDNode):
    """Takes in USD and filters out matching path or names"""
    bl_idname = 'usd.FilterNode'
    bl_label = "Filter USD"

    filter_path: bpy.props.StringProperty(
        name="Pattern",
        description="USD Path pattern. Use special characters means:\n"
                    "  * - any word or subword\n"
                    "  ** - several words separated by '/' or subword",
        default='**')

    def draw_buttons(self, context, layout):
        layout.prop(self, 'filter_path')

    def compute(self, **kwargs):
        from pxr import Usd, UsdGeom

        input_stage = self.get_input_link('Input', **kwargs)
        if not input_stage:
            return None

        # creating search regex pattern and getting filtered rpims
        prog = re.compile(self.filter_path.replace('*', '#')\
                                          .replace('/', '\/')\
                                          .replace('##', '[\w\/]*')\
                                          .replace('#', '\w*'))

        def get_child_prims(prim):
            if prog.fullmatch(str(prim.GetPath())):
                yield prim
                return

            for child in prim.GetAllChildren():
                yield from get_child_prims(child)

        prims = tuple(get_child_prims(input_stage.GetDefaultPrim()))
        if not prims:
            return None

        stage = self.cached_stage.create()
        UsdGeom.SetStageMetersPerUnit(stage, 1)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        filter_prim = stage.DefinePrim(f"/filter")
        stage.SetDefaultPrim(filter_prim)

        for i, prim in enumerate(prims, 1):
            ref = stage.DefinePrim(f"/filter/ref{i}", 'Xform')
            override_prim = stage.OverridePrim(str(ref.GetPath()) + '/' + prim.GetName())
            override_prim.GetReferences().AddReference(input_stage.GetRootLayer().realPath,
                                                       prim.GetPath())

        return stage
