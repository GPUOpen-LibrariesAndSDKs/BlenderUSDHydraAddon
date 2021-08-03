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
from pxr import Usd, UsdGeom, UsdSkel, Sdf

from .base_node import USDNode

from . import log

class RootNode(USDNode):
    """Create root primitive and make it parent for USD primitives"""
    bl_idname = 'usd.RootNode'
    bl_label = "Root"

    def update_data(self, context):
        self.reset()

    root_name: bpy.props.StringProperty(
        name='Name',
        description="Name for USD root primitive",
        default='Name',
        update=update_data
    )

    prim_type:  bpy.props.EnumProperty(
        items=(('Xform', 'Xform', 'USD primitive type'),
               ('Scope', 'Scope', 'USD primitive type'),
               ('SkelRoot', 'SkelRoot', 'USD primitive type'),
               ('None', 'None', 'USD primitive type')),
        default='Xform',
        description='Filter by type for USD primitives',
        name="Type",
        update=update_data
    )

    def draw_buttons(self, context, layout):
        layout.prop(self, 'root_name')
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

        if not self.root_name or not re.match("^[a-zA-Z]+.*", self.root_name):
            return None

        stage = self.cached_stage.create()
        UsdGeom.SetStageMetersPerUnit(stage, 1)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        root_prim = stage.GetPseudoRoot()

        # create new root prim according to root_name and type
        if self.prim_type == 'Xform':
            root_prim = UsdGeom.Xform.Define(stage, root_prim.GetPath().AppendChild(self.root_name))
        elif self.prim_type == 'Scope':
            root_prim = UsdGeom.Scope.Define(stage, root_prim.GetPath().AppendChild(self.root_name))
        elif self.prim_type == 'SkelRoot':
            root_prim = UsdSkel.Root.Define(stage, root_prim.GetPath().AppendChild(self.root_name))
        else:
            root_prim = stage.DefinePrim(f'/{self.root_name}')

        for i, prim in enumerate(prims, 1):
            override_prim = stage.OverridePrim(root_prim.GetPath().AppendChild(prim.GetName()))
            override_prim.GetReferences().AddReference(input_stage.GetRootLayer().realPath, prim.GetPath())

        return stage
