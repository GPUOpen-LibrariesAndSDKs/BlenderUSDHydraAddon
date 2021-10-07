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

from pxr import UsdGeom, Tf, Gf

from .base_node import USDNode
from .blender_data import (
    HDUSD_USD_NODETREE_OP_blender_data_link_object, HDUSD_USD_NODETREE_OP_blender_data_unlink_object)


class HDUSD_USD_NODETREE_MT_instancing_object(bpy.types.Menu):
    bl_idname = "HDUSD_USD_NODETREE_MT_instancing_object"
    bl_label = "Object"
    bl_description = "Object for scattering instances"

    def draw(self, context):
        layout = self.layout
        objects = context.scene.objects

        for obj in objects:
            if obj.hdusd.is_usd or obj.type not in "MESH":
                continue

            row = layout.row()
            op = row.operator(HDUSD_USD_NODETREE_OP_blender_data_link_object.bl_idname,
                              text=obj.name)
            op.object_name = obj.name


class InstancingNode(USDNode):
    """Create and distribute instances of primitives"""
    bl_idname = 'usd.InstancingNode'
    bl_label = "Instancing"

    def update_data(self, context):
        self.reset(True)

    name: bpy.props.StringProperty(
        name="Name",
        description="Name for USD instance primitive",
        default="Instance",
        update=update_data
    )

    object: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Object",
        description="Object for scattering instances",
        update=update_data
    )

    method: bpy.props.EnumProperty(
        name="Method",
        description="Object instancing method",
        items=(('VERTICES', "Vertices", "Instancing by vertices"),
               ('POLYGONS', "Faces", "Instancing by faces")),
        default='VERTICES',
        update=update_data
    )

    object_transform: bpy.props.BoolProperty(
        name="Use Object Transform",
        default=True,
        update=update_data,
        description="Apply object transform to instances",
    )

    def draw_buttons(self, context, layout):
        layout.prop(self, 'name')

        split = layout.row(align=True).split(factor=0.25)
        col = split.column()

        col.label(text="Object")
        col = split.column()
        row = col.row(align=True)
        if self.object:
            row.menu(HDUSD_USD_NODETREE_MT_instancing_object.bl_idname,
                     text=self.object.name, icon='OBJECT_DATAMODE')
            row.operator(HDUSD_USD_NODETREE_OP_blender_data_unlink_object.bl_idname, icon='X')
            layout.prop(self, 'method')
        else:
            row.menu(HDUSD_USD_NODETREE_MT_instancing_object.bl_idname,
                     text=" ", icon='OBJECT_DATAMODE')

        row = layout.row()
        row.alignment = 'LEFT'
        row.prop(self, 'object_transform')

    def compute(self, **kwargs):
        stage = self.cached_stage.create()
        UsdGeom.SetStageMetersPerUnit(stage, 1)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)

        if not self.object:
            return None

        input_stage = self.get_input_link('Input', **kwargs)

        if not input_stage:
            return None

        if not input_stage.GetPseudoRoot().GetAllChildren():
            return None

        distribute_items = self.object.data.vertices if self.method == 'VERTICES' else self.object.data.polygons
        if not distribute_items:
            return None

        for i, item in enumerate(distribute_items):
            root_xform = UsdGeom.Xform.Define(stage, f'/{Tf.MakeValidIdentifier(f"{self.name}_{i}")}')
            for prim in input_stage.GetPseudoRoot().GetAllChildren():
                override_prim = stage.OverridePrim(root_xform.GetPath().AppendChild(prim.GetName()))
                override_prim.GetReferences().AddReference(input_stage.GetRootLayer().realPath, prim.GetPath())

            trans = Matrix.Translation(item.co if self.method == 'VERTICES' else item.center)
            rot = item.normal.to_track_quat().to_matrix().to_4x4()

            transform = trans @ rot
            if self.object_transform:
                transform = self.object.matrix_world @ transform

            UsdGeom.Xform.Get(stage, root_xform.GetPath()).MakeMatrixXform()
            root_xform.GetPrim().GetAttribute('xformOp:transform').Set(Gf.Matrix4d(transform.transposed()))

        return stage

    def depsgraph_update(self, depsgraph):
        if not self.object:
            return

        obj = next((update.id for update in depsgraph.updates if isinstance(update.id, bpy.types.Object)
                    and not update.id.hdusd.is_usd and update.id.name == self.object.name), None)
        if obj:
            self.reset(True)
