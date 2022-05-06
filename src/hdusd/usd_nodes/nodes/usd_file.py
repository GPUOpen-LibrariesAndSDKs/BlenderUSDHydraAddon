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
import os
import re

import bpy
from pxr import Usd, UsdGeom, Sdf, Gf

from .base_node import USDNode
from . import log


class UsdFileNode(USDNode):
    ''' read USD file '''
    bl_idname = 'usd.UsdFileNode'
    bl_label = "USD File"
    bl_icon = "FILE"
    bl_width_default = 250
    bl_width_min = 250

    input_names = ()
    use_hard_reset = False

    def update_data(self, context):
        self.reset(True)

    filename: bpy.props.StringProperty(
        name="USD File",
        subtype='FILE_PATH',
        update=update_data,
    )

    filter_path: bpy.props.StringProperty(
        name="Pattern",
        description="USD Path pattern. Use special characters means:\n"
                    "  * - any word or subword\n"
                    "  ** - several words separated by '/' or subword",
        default='/*',
        update=update_data
    )

    def draw_buttons(self, context, layout):
        layout.prop(self, 'filename')
        layout.prop(self, 'filter_path')

    def compute(self, **kwargs):
        if not self.filename:
            return None

        file_path = bpy.path.abspath(self.filename)
        if not os.path.isfile(file_path):
            log.warn("Couldn't find USD file", self.filename, self)
            return None

        input_stage = Usd.Stage.Open(file_path)
        root_layer = input_stage.GetRootLayer()
        root_layer.TransferContent(input_stage.Flatten(False))

        if self.filter_path == '/*':
            self.cached_stage.insert(input_stage)
            return input_stage

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
        stage.SetInterpolationType(Usd.InterpolationTypeHeld)
        UsdGeom.SetStageMetersPerUnit(stage, 1)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)

        root_prim = stage.GetPseudoRoot()
        for i, prim in enumerate(prims, 1):
            override_prim = stage.OverridePrim(root_prim.GetPath().AppendChild(prim.GetName()))
            override_prim.GetReferences().AddReference(input_stage.GetRootLayer().realPath, prim.GetPath())

        return stage
