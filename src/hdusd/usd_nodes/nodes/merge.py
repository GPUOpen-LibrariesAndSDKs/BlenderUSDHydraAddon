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

from pxr import Usd, UsdGeom

from .base_node import USDNode


MAX_INPUTS_NUMBER = 10


class MergeNode(USDNode):
    """Merges two USD streams"""
    bl_idname = 'usd.MergeNode'
    bl_label = "Merge"

    input_names = tuple(f"Input {i + 1}" for i in range(MAX_INPUTS_NUMBER))

    def update_inputs_number(self, context):
        for i in range(MAX_INPUTS_NUMBER):
            if len(self.inputs) > self.inputs_number:
                self.inputs.remove(self.inputs[len(self.inputs) - 1])

            if len(self.inputs) < self.inputs_number:
                self.inputs.new(name=self.input_names[len(self.inputs)], type="NodeSocketShader")

    inputs_number: bpy.props.IntProperty(
        name="Inputs",
        min=2, max=MAX_INPUTS_NUMBER, default=2,
        update=update_inputs_number
    )

    def init(self, context):
        super().init(context)
        self.update_inputs_number(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'inputs_number')

    def compute(self, **kwargs):
        ref_stages = []
        for i in range(len(self.inputs)):
            stage = self.get_input_link(i, **kwargs)
            if stage:
                ref_stages.append(stage)

        if not ref_stages:
            return None

        if len(ref_stages) == 1:
            return ref_stages[0]

        stage = self.cached_stage.create()
        UsdGeom.SetStageMetersPerUnit(stage, 1)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)

        root_prim = stage.GetPseudoRoot()

        for ref_stage in ref_stages:
            for prim in ref_stage.GetPseudoRoot().GetAllChildren():
                override_prim = stage.OverridePrim(root_prim.GetPath().AppendChild(prim.GetName()))
                override_prim.GetReferences().AddReference(ref_stage.GetRootLayer().realPath, prim.GetPath())

        return stage

