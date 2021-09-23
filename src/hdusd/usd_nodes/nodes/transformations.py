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

    file_path: bpy.props.StringProperty(name="USD File", subtype='FILE_PATH')

    def draw_buttons(self, context, layout):
        layout.prop(self, 'file_path')

    def compute(self, **kwargs):
        stage = self.cached_stage.create()

        return stage


class OffsetterNode(USDNode):
    """Offsets input data"""
    bl_idname = 'usd.OffsetterNode'
    bl_label = "Offsetter"

    file_path: bpy.props.StringProperty(name="USD File", subtype='FILE_PATH')

    def draw_buttons(self, context, layout):
        layout.prop(self, 'file_path')

    def compute(self, **kwargs):
        stage = self.cached_stage.create()

        return stage


class RotatorNode(USDNode):
    """Rotates input data"""
    bl_idname = 'usd.RotatorNode'
    bl_label = "Rotator"

    file_path: bpy.props.StringProperty(name="USD File", subtype='FILE_PATH')

    def draw_buttons(self, context, layout):
        layout.prop(self, 'file_path')

    def compute(self, **kwargs):
        stage = self.cached_stage.create()

        return stage


class ScalerNode(USDNode):
    """Scales input data"""
    bl_idname = 'usd.ScalerNode'
    bl_label = "Scaler"

    file_path: bpy.props.StringProperty(name="USD File", subtype='FILE_PATH')

    def draw_buttons(self, context, layout):
        layout.prop(self, 'file_path')

    def compute(self, **kwargs):
        stage = self.cached_stage.create()

        return stage


class AffinerNode(USDNode):
    """Affine transformations of input data"""
    bl_idname = 'usd.AffinerNode'
    bl_label = "Affiner"

    file_path: bpy.props.StringProperty(name="USD File", subtype='FILE_PATH')

    def draw_buttons(self, context, layout):
        layout.prop(self, 'file_path')

    def compute(self, **kwargs):
        stage = self.cached_stage.create()

        return stage