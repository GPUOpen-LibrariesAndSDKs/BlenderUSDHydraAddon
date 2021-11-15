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

from mathutils import Matrix

from pxr import Usd, UsdGeom, Tf, Gf

from .base_node import USDNode

from ...export.object import get_transform

class HDUSD_USD_NODETREE_OP_transform_add_empty(bpy.types.Operator):
    """Add new Empty object"""
    bl_idname = "hdusd.usd_nodetree_transform_add_empty"
    bl_label = ""

    def execute(self, context):
        obj = bpy.data.objects.new('Empty', None)        
        context.view_layer.active_layer_collection.collection.objects.link(obj)
        context.node.object = bpy.data.objects[obj.name_full]
        for sel_obj in context.selected_objects:
            sel_obj.select_set(False)
        context.view_layer.objects.active = obj
        obj.select_set(True)

        return {"FINISHED"}


class TransformNode(USDNode):
    """Transforms input data"""
    bl_idname = 'usd.TransformNode'
    bl_label = "Transform"
    bl_icon = "OBJECT_ORIGIN"
    bl_width_default = 250

    def update_data(self, context):
        self.reset()

    name: bpy.props.StringProperty(
        name="Name",
        description="Xform name for USD root primitive",
        default="Transform",
        update=update_data
    )

    translation: bpy.props.FloatVectorProperty(update=update_data, unit='LENGTH')
    rotation: bpy.props.FloatVectorProperty(update=update_data, unit='ROTATION')
    scale: bpy.props.FloatVectorProperty(update=update_data, unit='NONE', default=(1.0, 1.0, 1.0))

    def draw_buttons(self, context, layout):
        col = layout.column()
        col.prop(self, 'name')
        col.separator()
        col.row().prop(self, 'translation', text='Translation')
        col.row().prop(self, 'rotation', text='Rotation')
        col.row().prop(self, 'scale', text='Scale')

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

        translation = Matrix.Translation((self.translation[:3]))

        diagonal = Matrix.Diagonal((self.scale[:3])).to_4x4()

        rotation_x = Matrix.Rotation(self.rotation[0], 4, 'X')
        rotation_y = Matrix.Rotation(self.rotation[1], 4, 'Y')
        rotation_z = Matrix.Rotation(self.rotation[2], 4, 'Z')

        transform = translation @ rotation_x @ rotation_y @ rotation_z @ diagonal

        UsdGeom.Xform.Get(stage, root_xform.GetPath()).AddTransformOp()
        root_prim.GetAttribute('xformOp:transform').Set(Gf.Matrix4d(transform.transposed()))

        return stage


class TransformByEmptyNode(USDNode):
    """Transforms input data based on Empty object"""
    bl_idname = 'usd.TransformByEmptyNode'
    bl_label = "Transform by Empty object"
    bl_icon = "OBJECT_ORIGIN"

    def update_data(self, context):
        for sel_obj in context.selected_objects:
            sel_obj.select_set(False)
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
            UsdGeom.Xform.Get(stage, root_xform.GetPath()).AddTransformOp()
            root_prim.GetAttribute('xformOp:transform').Set(Gf.Matrix4d(get_transform(obj)))

        return stage

    def depsgraph_update(self, depsgraph):
        if not self.object:
            return

        obj = next((update.id for update in depsgraph.updates if isinstance(update.id, bpy.types.Object)
                    and not update.id.hdusd.is_usd and update.id.name == self.object.name), None)
        if obj:
            self.reset()
