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
import mathutils

from pxr import Usd, UsdGeom, Gf

from . import HdUSDProperties
from . import usd_list
from ..export.object import get_transform


class ObjectProperties(HdUSDProperties):
    bl_type = bpy.types.Object

    is_usd: bpy.props.BoolProperty(default=False)
    usd_id: bpy.props.IntProperty(default=-1)
    sdf_path: bpy.props.StringProperty(default="/")

    def sync(self, prim):
        context = bpy.context
        prim_obj = self.id_data

        if not prim or str(prim.GetTypeName()) != 'Xform':
            self.usd_id = -1
            prim_obj.name = self.sdf_path = "/"
            prim_obj.matrix_world = mathutils.Matrix.Identity(4)

            # hiding, deactivating and deselecting prim object
            prim_obj.hide_viewport = True
            if prim_obj in context.selected_objects:
                prim_obj.select_set(False)
            if bpy.context.view_layer.objects.active == prim_obj:
                bpy.context.view_layer.objects.active = None
            return

        self.usd_id = usd_list._stage_cache.GetId(prim.GetStage()).ToLongInt()
        prim_obj.name = self.sdf_path = str(prim.GetPath())
        prim_obj.matrix_world = UsdGeom.Xform(prim).GetOrderedXformOps()[0].Get()

        # showing, activating and selecting prim object
        prim_obj.hide_viewport = False
        context.view_layer.objects.active = prim_obj
        if len(context.selected_objects) < 2:
            if context.selected_objects:
                context.selected_objects[0].select_set(False)
            prim_obj.select_set(True)

    def update_prim(self):
        if self.usd_id == -1:
            return

        obj = self.id_data
        stage = usd_list._stage_cache.Find(Usd.StageCache.Id.FromLongInt(self.usd_id))
        prim = stage.GetPrimAtPath(self.sdf_path)

        xform = UsdGeom.Xform(prim)
        xform.ClearXformOpOrder()
        xform.AddTransformOp().Set(Gf.Matrix4d(get_transform(obj)))
