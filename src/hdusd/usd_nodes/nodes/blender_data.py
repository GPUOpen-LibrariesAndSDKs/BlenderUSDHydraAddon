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

from pxr import UsdGeom

from .base_node import USDNode
from ...export import object
from ...utils import depsgraph_objects


class BlenderDataNode(USDNode):
    """Blender data to USD can export whole scene, one collection or object"""
    bl_idname = 'usd.BlenderDataNode'
    bl_label = "Blender Data"

    input_names = ()
    use_hard_reset = False

    def update_data(self, context):
        self.reset(True)

    export_type: bpy.props.EnumProperty(
        name="Data",
        description="Blender Data to read",
        items=(('SCENE', "Scene", "Read entire scene"),
            ('COLLECTION', "Collection", "Read collection"),
            ('OBJECT', 'Object', "Read single object"),
        ),
        default='SCENE',
        update=update_data
    )
    collection_to_export: bpy.props.PointerProperty(
        type=bpy.types.Collection,
        name="Collection",
        description="",
        update=update_data
    )
    object_to_export: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Object",
        description="",
        update=update_data
    )

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        col.prop(self, 'export_type')
        if self.export_type == 'COLLECTION':
            col.prop(self, 'collection_to_export')
        elif self.export_type == 'OBJECT':
            col.prop(self, 'object_to_export')

    def compute(self, **kwargs):
        depsgraph = bpy.context.evaluated_depsgraph_get()

        stage = self.cached_stage.create()
        UsdGeom.SetStageMetersPerUnit(stage, 1)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)

        root_prim = stage.GetPseudoRoot()

        if self.export_type == 'SCENE':
            for obj in depsgraph_objects(depsgraph):
                object.sync(root_prim, obj)

        elif self.export_type == 'COLLECTION':
            if not self.collection_to_export:
                return

            for obj_col in self.collection_to_export.objects:
                if obj_col.hdusd.is_usd:
                    continue

                object.sync(root_prim, obj_col.evaluated_get(depsgraph))

        elif self.export_type == 'OBJECT':
            if not self.object_to_export or self.object_to_export.hdusd.is_usd:
                return

            object.sync(root_prim, self.object_to_export.evaluated_get(depsgraph))

        return stage

    def depsgraph_update(self, depsgraph):
        stage = self.cached_stage()
        if not stage:
            self.final_compute()
            return

        is_updated = False

        root_prim = stage.GetPseudoRoot()

        for update in depsgraph.updates:
            if isinstance(update.id, bpy.types.Object):
                obj = update.id
                if obj.hdusd.is_usd:
                    continue

                # checking if object has to be updated
                if self.export_type == 'COLLECTION':
                    if not self.collection_to_export or \
                            obj.name not in self.collection_to_export.objects:
                        continue

                elif self.export_type == 'OBJECT':
                    if not self.object_to_export or \
                            object.sdf_name(self.object_to_export) != object.sdf_name(obj):
                        continue

                # updating object
                object.sync_update(root_prim, obj,
                                   update.is_updated_geometry, update.is_updated_transform)

                is_updated = True

            elif isinstance(update.id, bpy.types.Collection):
                coll = update.id

                current_keys = set(prim.GetName() for prim in root_prim.GetAllChildren())
                required_keys = set()
                depsgraph_keys = set(object.sdf_name(obj)
                                     for obj in depsgraph_objects(depsgraph))

                if self.export_type == 'SCENE':
                    required_keys = depsgraph_keys

                elif self.export_type == 'COLLECTION':
                    if not self.collection_to_export:
                        continue

                    if coll.name != self.collection_to_export.name:
                        continue

                    required_keys = set(object.sdf_name(obj) for obj in coll.objects)
                    required_keys.intersection_update(depsgraph_keys)

                elif self.export_type == 'OBJECT':
                    if not self.object_to_export:
                        continue

                    if object.sdf_name(self.object_to_export) in depsgraph_keys:
                        required_keys = {object.sdf_name(self.object_to_export)}

                keys_to_remove = current_keys - required_keys
                keys_to_add = required_keys - current_keys

                if keys_to_remove:
                    for key in keys_to_remove:
                        root_prim.GetStage().RemovePrim(f"{root_prim.GetPath()}/{key}")

                    is_updated = True

                if keys_to_add:
                    for obj in depsgraph_objects(depsgraph):
                        obj_key = object.sdf_name(obj)
                        if obj_key not in keys_to_add:
                            continue

                        object.sync(root_prim, obj)

                    is_updated = True

        if is_updated:
            self.hdusd.usd_list.update_items()
            self._reset_next(True)
