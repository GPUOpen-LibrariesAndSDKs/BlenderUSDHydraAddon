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

from mathutils import Matrix

from pxr import Usd, UsdGeom, Tf, Gf

from .base_node import USDNode


class HDUSD_USD_NODETREE_OP_transform_add_empty(bpy.types.Operator):
    """Add new Empty object"""
    bl_idname = "hdusd.usd_nodetree_transform_add_empty"
    bl_label = ""

    def execute(self, context):
        bpy.ops.object.add(type='EMPTY')
        return {"FINISHED"}


class TransformNode(USDNode):
    """Transforms input data"""
    bl_idname = 'usd.TransformNode'
    bl_label = "Transform"
    bl_icon = "OBJECT_ORIGIN"
    bl_width_default = 305

    def update_data(self, context):
        self.reset()

    # region properties
    name: bpy.props.StringProperty(
        name="Xform name",
        description="Name for USD root primitive",
        default="Transform",
        update=update_data
    )

    translation_x: bpy.props.FloatProperty(update=update_data, subtype='DISTANCE')
    translation_y: bpy.props.FloatProperty(update=update_data, subtype='DISTANCE')
    translation_z: bpy.props.FloatProperty(update=update_data, subtype='DISTANCE')

    rotation_y: bpy.props.FloatProperty(update=update_data, subtype='ANGLE')
    rotation_z: bpy.props.FloatProperty(update=update_data, subtype='ANGLE')
    rotation_x: bpy.props.FloatProperty(update=update_data, subtype='ANGLE')

    scale_x: bpy.props.FloatProperty(update=update_data, default=1.0)
    scale_y: bpy.props.FloatProperty(update=update_data, default=1.0)
    scale_z: bpy.props.FloatProperty(update=update_data, default=1.0)
    # endregion

    def draw_buttons(self, context, layout):
        layout.prop(self, 'name')

        split = layout.split(factor=0.20)
        col1 = split.column()
        col2 = split.column()

        col1.label(text='Translation')
        col1.label(text='Rotation')
        col1.label(text='Scale')

        row = col2.row(align=True)
        row.prop(self, 'translation_x', text='')
        row.prop(self, 'translation_y', text='')
        row.prop(self, 'translation_z', text='')

        row = col2.row(align=True)
        row.prop(self, 'rotation_x', text='')
        row.prop(self, 'rotation_y', text='')
        row.prop(self, 'rotation_z', text='')

        row = col2.row(align=True)
        row.prop(self, 'scale_x', text='')
        row.prop(self, 'scale_y', text='')
        row.prop(self, 'scale_z', text='')

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

        translation = Matrix.Translation((self.translation_x,
                                          self.translation_y,
                                          self.translation_z))

        diagonal = Matrix.Diagonal((self.scale_x,
                                    self.scale_y,
                                    self.scale_z)).to_4x4()

        rotation_x = Matrix.Rotation(self.rotation_x, 4, 'X')
        rotation_y = Matrix.Rotation(self.rotation_y, 4, 'Y')
        rotation_z = Matrix.Rotation(self.rotation_z, 4, 'Z')

        transform = translation @ rotation_x @ rotation_y @ rotation_z @ diagonal

        transform = transform.transposed()

        usd_geom.AddTransformOp()
        matrix = Gf.Matrix4d(transform[0][0], transform[0][1], transform[0][2], 0,
                             transform[1][0], transform[1][1], transform[1][2], 0,
                             transform[2][0], transform[2][1], transform[2][2], 0,
                             transform[3][0], transform[3][1], transform[3][2], 1)
        root_prim.GetAttribute('xformOp:transform').Set(matrix)

        return stage


class TransformByEmptyNode(USDNode):
    """Transforms input data based on Empty object"""
    bl_idname = 'usd.TransformByEmptyNode'
    bl_label = "Transform by Empty object"
    bl_icon = "OBJECT_ORIGIN"

    def update_data(self, context):
        self.reset()

    def is_empty_obj(self, object):
        return object.type == 'EMPTY' and not object.hdusd.is_usd

    name: bpy.props.StringProperty(
        name="Xform name",
        description="Name for USD root primitive",
        default="Transform",
        update=update_data
    )

    object: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Object",
        description="Object for scattering instances",
        update=update_data,
        poll=is_empty_obj
    )

    def draw_buttons(self, context, layout):
        layout.prop(self, 'name')
        row = layout.row(align=True)
        if self.object:
            row.prop(self, 'object')
        else:
            row.prop(self, 'object')
            row.operator(HDUSD_USD_NODETREE_OP_transform_add_empty.bl_idname, icon='OUTLINER_OB_EMPTY')

    def compute(self, **kwargs):
        input_stage = self.get_input_link('Input', **kwargs)

        if not input_stage or not self.name:
            return None

        if not self.object:
            return input_stage

        depsgraph = bpy.context.evaluated_depsgraph_get()
        obj = self.object.evaluated_get(depsgraph)

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

        if obj:
            usd_geom = UsdGeom.Xform.Get(stage, root_xform.GetPath())
            usd_geom.AddTransformOp()
            obj_matrix = obj.matrix_world.transposed()
            matrix = Gf.Matrix4d(obj_matrix[0][0], obj_matrix[0][1], obj_matrix[0][2], 0,
                                 obj_matrix[1][0], obj_matrix[1][1], obj_matrix[1][2], 0,
                                 obj_matrix[2][0], obj_matrix[2][1], obj_matrix[2][2], 0,
                                 obj_matrix[3][0], obj_matrix[3][1], obj_matrix[3][2], 1)
            root_prim.GetAttribute('xformOp:transform').Set(matrix)

        return stage
