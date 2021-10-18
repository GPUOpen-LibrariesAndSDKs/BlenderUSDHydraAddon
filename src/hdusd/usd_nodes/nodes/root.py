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
from pxr import Usd, UsdGeom, UsdSkel, Sdf, Tf

from .base_node import USDNode

from . import log


class RootNode(USDNode):
    """Create root primitive and make it parent for USD primitives"""
    bl_idname = 'usd.RootNode'
    bl_label = "Root"
    bl_icon = "COLLECTION_NEW"

    def update_data(self, context):
        self.reset()

    name: bpy.props.StringProperty(
        name="Name",
        description="Name for USD root primitive",
        default="Root",
        update=update_data
    )
    type:  bpy.props.EnumProperty(
        name="Type",
        description="Filter by type for USD primitives",
        items=(('Xform', "Xform", "Xform primitive type"),
               ('Scope', "Scope", "Scope primitive type"),
               ('SkelRoot', "SkelRoot", "SkelRoot primitive type"),
               ('None', "None", "No primitive type")),
        default='Xform',
        update=update_data
    )

    def draw_buttons(self, context, layout):
        layout.prop(self, 'name')
        layout.prop(self, 'type')

    def compute(self, **kwargs):
        input_stage = self.get_input_link('Input', **kwargs)

        if not input_stage:
            return None

        if not self.name:
            return input_stage

        path = f'/{Tf.MakeValidIdentifier(self.name)}'
        stage = self.cached_stage.create()
        UsdGeom.SetStageMetersPerUnit(stage, 1)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)

        # create new root prim according to name and type
        if self.type == 'Xform':
            root_prim = UsdGeom.Xform.Define(stage, path)
        elif self.type == 'Scope':
            root_prim = UsdGeom.Scope.Define(stage, path)
        elif self.type == 'SkelRoot':
            root_prim = UsdSkel.Root.Define(stage, path)
        else:
            root_prim = stage.DefinePrim(path)

        for prim in input_stage.GetPseudoRoot().GetAllChildren():
            override_prim = stage.OverridePrim(root_prim.GetPath().AppendChild(prim.GetName()))
            override_prim.GetReferences().AddReference(input_stage.GetRootLayer().realPath, prim.GetPath())

        return stage
