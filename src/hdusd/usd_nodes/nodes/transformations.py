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

    def update_data(self, context):
        self.reset()

    def set_x(self, value):
        self["offset_x"] = value

    def set_y(self, value):
        self["offset_y"] = value

    def set_z(self, value):
        self["offset_z"] = value

    def get_x(self):
        return self.get("offset_x", 0.0)

    def get_y(self):
        return self.get("offset_y", 0.0)

    def get_z(self):
        return self.get("offset_z", 0.0)

    offset_x: bpy.props.FloatProperty(name="X offset", set=set_x, get=get_x, update=update_data)
    offset_y: bpy.props.FloatProperty(name="Y offset", set=set_y, get=get_y, update=update_data)
    offset_z: bpy.props.FloatProperty(name="Z offset", set=set_z, get=get_z, update=update_data)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'offset_x')
        layout.prop(self, 'offset_y')
        layout.prop(self, 'offset_z')

    def compute(self, **kwargs):
        stage = self.get_input_link('Input', **kwargs)

        if stage is not None:

            for prim in stage.TraverseAll():
                usd_geom = UsdGeom.Xform.Get(stage, prim.GetPath())

                if prim.GetTypeName() == 'Mesh':

                    if not prim.HasAttribute('xformOp:translate'):
                        usd_geom.AddTranslateOp()

                    prim.GetAttribute('xformOp:translate').Set(
                        (self.offset_x, self.offset_y, self.offset_z))

        return stage


class RotatorNode(USDNode):
    """Rotates input data"""
    bl_idname = 'usd.RotatorNode'
    bl_label = "Rotator"

    def update_data(self, context):
        self.reset()

    def set_x(self, value):
        self["rotate_x"] = value

    def set_y(self, value):
        self["rotate_y"] = value

    def set_z(self, value):
        self["rotate_z"] = value

    def get_x(self):
        return self.get("rotate_x", 0.0)

    def get_y(self):
        return self.get("rotate_y", 0.0)

    def get_z(self):
        return self.get("rotate_z", 0.0)

    rotate_x: bpy.props.FloatProperty(name="X origin", set=set_x, get=get_x, update=update_data)
    rotate_y: bpy.props.FloatProperty(name="Y origin", set=set_y, get=get_y, update=update_data)
    rotate_z: bpy.props.FloatProperty(name="Z origin", set=set_z, get=get_z, update=update_data)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'rotate_x')
        layout.prop(self, 'rotate_y')
        layout.prop(self, 'rotate_z')

    def compute(self, **kwargs):
        stage = self.get_input_link('Input', **kwargs)

        if stage is not None:

            for prim in stage.TraverseAll():
                usd_geom = UsdGeom.Xform.Get(stage, prim.GetPath())

                if prim.GetTypeName() == 'Mesh':

                    if not prim.HasAttribute('xformOp:rotateXYZ'):
                        usd_geom.AddRotateXYZOp()

                    prim.GetAttribute('xformOp:rotateXYZ').Set((self.rotate_x, self.rotate_y, self.rotate_z))

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