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
    """Create instances of object"""
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
        items={('vertices', "Vertices", ""),
               ('polygons', "Faces", "")},
        default='vertices',
        update=update_data
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

    def compute(self, **kwargs):
        stage = self.cached_stage.create()
        UsdGeom.SetStageMetersPerUnit(stage, 1)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)

        if not self.object:
            return

        input_stage = self.get_input_link('Input', **kwargs)

        if not input_stage:
            return

        if not len(list(input_stage.TraverseAll())):
            return

        distribute_items = getattr(self.object.data, self.method, None)
        if distribute_items is None or not len(distribute_items):
            return

        matrix_world = self.object.matrix_world

        for item in distribute_items:
            prim_mame = f"/{self.name}_{item.index}"
            root_xform = UsdGeom.Xform.Define(stage, prim_mame)
            for prim in input_stage.GetPseudoRoot().GetAllChildren():
                override_prim = stage.OverridePrim(root_xform.GetPath().AppendChild(prim.GetName()))
                override_prim.GetReferences().AddReference(input_stage.GetRootLayer().realPath, prim.GetPath())

            t = Matrix.Translation(matrix_world @ (item.co if self.method == 'vertices' else item.center))
            q = (matrix_world.inverted_safe().transposed().to_3x3() @ item.normal).to_track_quat().to_matrix().to_4x4()
            m = t @ q

            UsdGeom.Xform.Get(stage, root_xform.GetPath()).MakeMatrixXform()
            root_xform.GetPrim().GetAttribute('xformOp:transform').Set(Gf.Matrix4d(m.transposed()))

        return stage

    def depsgraph_update(self, depsgraph):
        for update in depsgraph.updates:
            if isinstance(update.id, bpy.types.Object):
                obj = update.id
                if obj.hdusd.is_usd:
                    continue

                if obj.name == self.object.name:
                    self.reset(True)
