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

from pxr import UsdGeom, Gf

from . import HdUSDProperties, CachedStageProp
from ..export.object import get_transform
from ..mx_nodes.node_tree import MxNodeTree


class ObjectProperties(HdUSDProperties):
    bl_type = bpy.types.Object

    is_usd: bpy.props.BoolProperty(default=False)
    sdf_path: bpy.props.StringProperty(default="/")
    cached_stage: bpy.props.PointerProperty(type=CachedStageProp)

    material_x: bpy.props.PointerProperty(type=MxNodeTree)

    def sync_from_prim(self, prim, context):
        prim_obj = self.id_data

        if not prim or str(prim.GetTypeName()) != 'Xform':
            self.cached_stage.clear()
            prim_obj.name = self.sdf_path = "/"
            prim_obj.matrix_world = mathutils.Matrix.Identity(4)

            # hiding, deactivating and deselecting prim object
            prim_obj.hide_viewport = True
            prim_obj.select_set(False)
            if context.view_layer.objects.active == prim_obj:
                context.view_layer.objects.active = None
            return

        self.cached_stage.assign(prim.GetStage())
        prim_obj.name = self.sdf_path = str(prim.GetPath())
        xform = UsdGeom.Xform(prim)
        ops = xform.GetOrderedXformOps()
        if ops:
            prim_obj.matrix_world = mathutils.Matrix(ops[0].Get()).transposed()
        else:
            prim_obj.matrix_world = mathutils.Matrix.Identity(4)

        # showing, activating and selecting prim object
        prim_obj.hide_viewport = False
        context.view_layer.objects.active = prim_obj
        if len(context.selected_objects) < 2:
            if context.selected_objects:
                context.selected_objects[0].select_set(False)
            prim_obj.select_set(True)

    def sync_to_prim(self):
        stage = self.cached_stage()
        if not stage:
            return

        obj = self.id_data
        prim = stage.GetPrimAtPath(self.sdf_path)

        xform = UsdGeom.Xform(prim)
        xform.MakeMatrixXform().Set(Gf.Matrix4d(get_transform(obj)))
