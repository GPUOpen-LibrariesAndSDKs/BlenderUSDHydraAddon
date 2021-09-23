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

class TransformNode(USDNode):
    """Transforms input data"""
    bl_idname = 'usd.TransformNode'
    bl_label = "Transform"

    offset_x: bpy.props.FloatProperty(name="X offset")
    offset_y: bpy.props.FloatProperty(name="Y offset")
    offset_z: bpy.props.FloatProperty(name="Z offset")

    rotate_x: bpy.props.FloatProperty(name="X origin")
    rotate_y: bpy.props.FloatProperty(name="Y origin")
    rotate_z: bpy.props.FloatProperty(name="Z origin")

    scale_x: bpy.props.FloatProperty(name="X axis")
    scale_y: bpy.props.FloatProperty(name="Y axis")
    scale_z: bpy.props.FloatProperty(name="Z axis")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'offset_x')
        layout.prop(self, 'offset_y')
        layout.prop(self, 'offset_z')

        layout.prop(self, 'rotate_x')
        layout.prop(self, 'rotate_y')
        layout.prop(self, 'rotate_z')

        layout.prop(self, 'scale_x')
        layout.prop(self, 'scale_y')
        layout.prop(self, 'scale_z')

    def compute(self, **kwargs):
        stage = self.cached_stage.create()

        return stage


class OffsetterNode(USDNode):
    """Offsets input data"""
    bl_idname = 'usd.OffsetterNode'
    bl_label = "Offsetter"

    offset_x: bpy.props.FloatProperty(name="X offset")
    offset_y: bpy.props.FloatProperty(name="Y offset")
    offset_z: bpy.props.FloatProperty(name="Z offset")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'offset_x')
        layout.prop(self, 'offset_y')
        layout.prop(self, 'offset_z')

    def compute(self, **kwargs):
        stage = self.cached_stage.create()

        return stage


class RotatorNode(USDNode):
    """Rotates input data"""
    bl_idname = 'usd.RotatorNode'
    bl_label = "Rotator"

    rotate_x: bpy.props.FloatProperty(name="X origin")
    rotate_y: bpy.props.FloatProperty(name="Y origin")
    rotate_z: bpy.props.FloatProperty(name="Z origin")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'rotate_x')
        layout.prop(self, 'rotate_y')
        layout.prop(self, 'rotate_z')

    def compute(self, **kwargs):
        stage = self.cached_stage.create()

        return stage


class ScalerNode(USDNode):
    """Scales input data"""
    bl_idname = 'usd.ScalerNode'
    bl_label = "Scaler"

    scale_x: bpy.props.FloatProperty(name="X axis")
    scale_y: bpy.props.FloatProperty(name="Y axis")
    scale_z: bpy.props.FloatProperty(name="Z axis")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'scale_x')
        layout.prop(self, 'scale_y')
        layout.prop(self, 'scale_z')

    def compute(self, **kwargs):
        stage = self.cached_stage.create()

        return stage


class AffinerNode(USDNode):
    """Affine transformations of input data"""
    bl_idname = 'usd.AffinerNode'
    bl_label = "Affiner"
    bl_description = 'Coefficients <A>, <F> and <K> must be non-zero.'

    A: bpy.props.FloatProperty(name="Ax")
    B: bpy.props.FloatProperty(name="By")
    C: bpy.props.FloatProperty(name="Cz")
    D: bpy.props.FloatProperty(name="D")

    E: bpy.props.FloatProperty(name="Ex")
    F: bpy.props.FloatProperty(name="Fy")
    G: bpy.props.FloatProperty(name="Gz")
    H: bpy.props.FloatProperty(name="H")

    I: bpy.props.FloatProperty(name="Ix")
    J: bpy.props.FloatProperty(name="Jy")
    K: bpy.props.FloatProperty(name="Kz")
    L: bpy.props.FloatProperty(name="L")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'A')
        layout.prop(self, 'B')
        layout.prop(self, 'C')
        layout.prop(self, 'D')

        layout.prop(self, 'E')
        layout.prop(self, 'F')
        layout.prop(self, 'G')
        layout.prop(self, 'H')

        layout.prop(self, 'I')
        layout.prop(self, 'J')
        layout.prop(self, 'K')
        layout.prop(self, 'L')

    def compute(self, **kwargs):
        stage = self.cached_stage.create()

        return stage