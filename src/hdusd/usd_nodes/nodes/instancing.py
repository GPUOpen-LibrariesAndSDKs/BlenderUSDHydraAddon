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
from ...export import object
from ...export.object import ObjectData


class HDUSD_USD_NODETREE_OP_blender_unlink_object(bpy.types.Operator):
    """Unlink object"""
    bl_idname = "hdusd.usd_nodetree_blender_unlink_object"
    bl_label = ""

    def execute(self, context):
        context.node.object = None
        return {"FINISHED"}


class HDUSD_USD_NODETREE_OP_blender_object(bpy.types.Operator):
    """Link object"""
    bl_idname = "hdusd.usd_nodetree_blender_object"
    bl_label = ""

    object_name: bpy.props.StringProperty(default="")

    def execute(self, context):
        context.node.object = bpy.data.objects[self.object_name]
        return {"FINISHED"}


class HDUSD_USD_NODETREE_MT_blender_object(bpy.types.Menu):
    bl_idname = "HDUSD_USD_NODETREE_MT_blender_object"
    bl_label = "Object"

    def draw(self, context):
        layout = self.layout
        objects = bpy.data.objects

        for obj in objects:
            if obj.hdusd.is_usd or obj.type not in "MESH":
                continue

            row = layout.row()
            op = row.operator(HDUSD_USD_NODETREE_OP_blender_object.bl_idname,
                              text=obj.name)
            op.object_name = obj.name


class InstancingNode(USDNode):
    """Create instance of scene, object"""
    bl_idname = 'usd.InstancingNode'
    bl_label = "Instancing"

    def update_data(self, context):
        self.reset()

    name: bpy.props.StringProperty(
        name="Name",
        description="Name for USD instance primitive",
        default="Instance",
        update=update_data
    )

    object: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Object",
        description="",
        update=update_data
    )

    method: bpy.props.EnumProperty(
        name="Method",
        description="Metod of instance distribution",
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
            row.menu(HDUSD_USD_NODETREE_MT_blender_object.bl_idname,
                     text=self.object.name, icon='OBJECT_DATAMODE')
            row.operator(HDUSD_USD_NODETREE_OP_blender_unlink_object.bl_idname, icon='X')
            layout.prop(self, 'method')
        else:
            row.menu(HDUSD_USD_NODETREE_MT_blender_object.bl_idname,
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

        distribute_items = getattr(self.object.data, self.method, None)
        if distribute_items is None or not len(distribute_items):
            return

        root_path = f'/{Tf.MakeValidIdentifier(self.name)}'
        root_prim = UsdGeom.Xform.Define(stage, root_path)

        prim = next((prim for prim in input_stage.GetPseudoRoot().GetAllChildren()
                 if prim.GetTypeName() in "Xform"))

        usd_matrix = prim.GetAttribute('xformOp:transform').Get()
        prim_t, prim_r, prim_s = Matrix(usd_matrix).transposed().decompose()

        for item in distribute_items:
            q = (item.normal.to_track_quat() @ prim_r).to_matrix().to_4x4()
            t = Matrix.Translation(prim_t + (item.co if self.method == 'vertices' else item.center))
            m = t @ q @ Matrix.Diagonal(prim_s.to_4d())

            prim_mame = f"{root_prim.GetPath().AppendChild(prim.GetName())}_{self.name}_{item.index}"
            override_prim = stage.OverridePrim(prim_mame)
            override_prim.GetReferences().AddReference(input_stage.GetRootLayer().realPath, prim.GetPath())
            override_prim.GetAttribute('xformOp:transform').Set(Gf.Matrix4d(m.transposed()))

        return stage

    def depsgraph_update(self, depsgraph):
        stage = self.cached_stage()
        if not stage:
            self.final_compute()
            return

        is_updated = False

        root_prim = stage.GetPseudoRoot()
        kwargs = {'scene': depsgraph.scene}

        for update in depsgraph.updates:
            if isinstance(update.id, bpy.types.Object):
                obj = update.id
                if obj.hdusd.is_usd:
                    continue

                obj_data = ObjectData.from_object(obj)
                # checking if object has to be updated

                if not self.object or \
                        ObjectData.from_object(self.object).sdf_name != obj_data.sdf_name:
                    continue
                # updating object
                object.sync_update(root_prim, obj_data,
                                   update.is_updated_geometry, update.is_updated_transform,
                                   **kwargs)
                is_updated = True
                continue

        if is_updated:
            self.hdusd.usd_list.update_items()
            self._reset_next(True)
