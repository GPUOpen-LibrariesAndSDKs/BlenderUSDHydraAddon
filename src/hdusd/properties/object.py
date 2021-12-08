#**********************************************************************
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
#********************************************************************
import bpy

from pxr import UsdGeom, Gf, UsdShade

from . import HdUSDProperties, CachedStageProp
from ..export import object, material
from ..utils import usd as usd_utils


GEOM_TYPES = ('Xform', 'SkelRoot')


class ObjectProperties(HdUSDProperties):
    bl_type = bpy.types.Object

    sdf_path: bpy.props.StringProperty(default="")
    cached_stage: bpy.props.PointerProperty(type=CachedStageProp)

    def update_material(self, context):
        prim = self.get_prim()
        usd_mat = None
        if self.material:
            usd_mat = material.sync(prim, self.material, None)

        usd_utils.bind_material(prim, usd_mat)

    def poll_material(self, mat):
        return bool(mat.node_tree)

    material: bpy.props.PointerProperty(
        name="Material",
        description="Select material for USD mesh",
        type=bpy.types.Material,
        update=update_material,
        poll=poll_material
    )

    @property
    def is_usd(self):
        return bool(self.sdf_path)

    def get_prim(self):
        stage = self.cached_stage()
        if not stage:
            return None

        return stage.GetPrimAtPath(self.sdf_path)

    def sync_from_prim(self, root_obj, prim):
        prim_obj = self.id_data

        self.sdf_path = str(prim.GetPath())
        self.cached_stage.assign(prim.GetStage())

        prim_obj.name = prim.GetName()
        prim_obj.parent = root_obj
        prim_obj.matrix_local = usd_utils.get_xform_transform(UsdGeom.Xform(prim))
        prim_obj.hide_viewport = prim.GetTypeName() not in GEOM_TYPES

    def sync_to_prim(self):
        prim = self.get_prim()
        if not prim:
            return

        obj = self.id_data
        xform = UsdGeom.Xform(prim)
        xform.MakeMatrixXform().Set(Gf.Matrix4d(object.get_transform_local(obj)))


def depsgraph_update(depsgraph):
    if not depsgraph.updates:
        return

    upd = depsgraph.updates[0]
    obj = upd.id
    if not isinstance(obj, bpy.types.Object) or not obj.hdusd.is_usd:
        return

    obj.hdusd.sync_to_prim()
