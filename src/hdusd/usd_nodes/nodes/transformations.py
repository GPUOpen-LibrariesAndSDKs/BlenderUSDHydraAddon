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
import math

from pxr import Usd, UsdGeom, Tf

from .base_node import USDNode


class TransformNode(USDNode):
    """Transforms input data"""
    bl_idname = 'usd.TransformNode'
    bl_label = "Transform"
    bl_icon = "OBJECT_ORIGIN"

    def update_data(self, context):
        self.reset()

    # region properties
    name: bpy.props.StringProperty(
        name="Xform name",
        description="Name for USD root primitive",
        default="Transform",
        update=update_data
    )

    toggle_translation: bpy.props.BoolProperty(update=update_data)
    translation: bpy.props.FloatVectorProperty(update=update_data, subtype='TRANSLATION')

    toggle_rotation: bpy.props.BoolProperty(update=update_data)
    rotation: bpy.props.FloatVectorProperty(update=update_data, subtype='EULER')

    toggle_scale: bpy.props.BoolProperty(update=update_data)
    scale: bpy.props.FloatVectorProperty(update=update_data, default=(1, 1, 1), subtype='XYZ')
    # endregion

    def draw_buttons(self, context, layout):
        layout.prop(self, 'name')

        row = layout.row()
        row.alignment = 'LEFT'
        row.prop(self, 'toggle_translation', text='')
        row.label(text='Translation')

        if self.toggle_translation:
            col = layout.column(align=True)
            col.prop(self, 'translation', text='')

            layout.separator()

        row = layout.row()
        row.alignment = 'LEFT'
        row.prop(self, 'toggle_rotation', text='')
        row.label(text='Rotation')

        if self.toggle_rotation:
            col = layout.column(align=True)
            col.prop(self, 'rotation', text='')

            layout.separator()

        row = layout.row()
        row.alignment = 'LEFT'
        row.prop(self, 'toggle_scale', text='')
        row.label(text='Scale')

        if self.toggle_scale:
            col = layout.column(align=True)
            col.prop(self, 'scale', text='')

    def compute(self, **kwargs):
        input_stage = self.get_input_link('Input', **kwargs)

        if not input_stage or not self.name:
            return None

        path = f'/{Tf.MakeValidIdentifier(self.name)}'
        stage = self.cached_stage.create()
        UsdGeom.SetStageMetersPerUnit(stage, 1)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
        root_xform = UsdGeom.Xform.Define(stage, path)
        root_prim = root_xform.GetPrim()

        for prim in input_stage.GetPseudoRoot().GetAllChildren():
            override_prim = stage.OverridePrim(root_xform.GetPath().AppendChild(prim.GetName()))
            override_prim.GetReferences().AddReference(input_stage.GetRootLayer().realPath,
                                                       prim.GetPath())

        usd_geom = UsdGeom.Xform.Get(stage, root_xform.GetPath())

        if self.toggle_translation:
            usd_geom.AddTranslateOp()
            root_prim.GetAttribute('xformOp:translate').Set(self.translation[:3])

        if self.toggle_rotation:
            usd_geom.AddRotateXYZOp()
            rotation = tuple(math.degrees(rot) for rot in self.rotation)
            root_prim.GetAttribute('xformOp:rotateXYZ').Set(rotation)

        if self.toggle_scale:
            usd_geom.AddScaleOp()
            root_prim.GetAttribute('xformOp:scale').Set(self.scale[:3])

        return stage
