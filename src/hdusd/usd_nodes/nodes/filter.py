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


class FilterNode(USDNode):
    """Takes in USD and filters out matching path or names"""
    bl_idname = 'usd.FilterNode'
    bl_label = "Filter"
    bl_icon = "FILTER"

    def update_data(self, context):
        self.reset()

    filter_path: bpy.props.StringProperty(
        name="Pattern",
        description="USD Path pattern. Use special characters means:\n"
                    "  * - any word or subword\n"
                    "  ** - several words separated by '/' or subword",
        default='/*',
        update=update_data
    )

    def draw_buttons(self, context, layout):
        layout.prop(self, 'filter_path')

    def compute(self, **kwargs):
        input_stage = self.get_input_link('Input', **kwargs)
        if not input_stage:
            return None

        # creating search regex pattern and getting filtered rpims
        prog = re.compile(self.filter_path.replace('*', '#')        # temporary replacing '*' to '#'
                                          .replace('/', '\/')       # for correct regex pattern
                                          .replace('##', '[\w\/]*') # creation
                                          .replace('#', '\w*'))

        def get_child_prims(prim):
            if not prim.IsPseudoRoot() and prog.fullmatch(str(prim.GetPath())):
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


class FilterRootNode(USDNode):
    """Takes in USD and filters out matching path or names from root only"""
    bl_idname = 'usd.FilterRootNode'
    bl_label = "Filter Root"
    bl_icon = "FILTER"

    def update_data(self, context):
        self.reset()

    filter_names: bpy.props.StringProperty(
        name="Names",
        description="USD prims names. Use delimiter ',' to split input into separated names",
        default='',
        update=update_data
    )

    def draw_buttons(self, context, layout):
        layout.prop(self, 'filter_names')

    def compute(self, **kwargs):
        input_stage = self.get_input_link('Input', **kwargs)
        if not input_stage:
            return None

        if not self.filter_names:
            return input_stage

        filter_names = (name.strip().lower() for name in self.filter_names.split(','))

        prims = (child for child in input_stage.GetPseudoRoot().GetAllChildren()
                 if child.GetName().lower() not in filter_names)

        if not prims:
            return input_stage

        stage = self.cached_stage.create()
        UsdGeom.SetStageMetersPerUnit(stage, 1)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)

        root_prim = stage.GetPseudoRoot()

        for i, prim in enumerate(prims, 1):
            override_prim = stage.OverridePrim(root_prim.GetPath().AppendChild(prim.GetName()))
            override_prim.GetReferences().AddReference(input_stage.GetRootLayer().realPath, prim.GetPath())

        return stage
