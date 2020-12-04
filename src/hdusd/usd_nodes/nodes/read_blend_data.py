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
from ...export import depsgraph as dg, object, sdf_path

from . import log


class ReadBlendDataNode(USDNode):
    """Blender data to USD can export whole scene, one collection or object"""
    bl_idname = 'usd.ReadBlendDataNode'
    bl_label = "Read Blend Data"

    input_names = ()

    def update_export_data(self, context):
        depsgraph = bpy.context.evaluated_depsgraph_get()

        stage = self.cached_stage()
        objects_prim = stage.GetPrimAtPath(f"/{depsgraph.scene.name}/objects")
        for obj_prim in objects_prim.GetAllChildren():
            stage.RemovePrim(obj_prim.GetPath())

        if self.export_type == 'SCENE':
            for obj in dg.depsgraph_objects(depsgraph):
                try:
                    object.sync(objects_prim, obj)
                except Exception as e:
                    log.error(e)

        elif self.export_type == 'COLLECTION':
            if self.collection_to_export:
                for obj_col in self.collection_to_export.objects:
                    obj = obj_col.evaluated_get(depsgraph)
                    try:
                        object.sync(objects_prim, obj)
                    except Exception as e:
                        log.error(e)

        elif self.export_type == 'OBJECT':
            if self.object_to_export:
                obj = self.object_to_export.evaluated_get(depsgraph)
                try:
                    object.sync(objects_prim, obj)
                except Exception as e:
                    log.error(e)

        else:
            raise ValueError("Incorrect export_type", self.export_type)

    export_type: bpy.props.EnumProperty(
        name="Data to Read",
        description="",
        items=(('SCENE', "Scene", "Read entire scene"),
            ('COLLECTION', "Collection", "Read collection"),
            ('OBJECT', 'Object', "Read single object"),
        ),
        default='SCENE',
        update=update_export_data
    )

    collection_to_export: bpy.props.PointerProperty(
        type=bpy.types.Collection,
        name="Collection",
        description="",
        update=update_export_data
    )
    
    object_to_export: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Object",
        description="",
        update=update_export_data
    )

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        col.use_property_split = False
        col.use_property_decorate = False

        flow = layout.grid_flow(row_major=True, even_columns=True, align=True)
        flow.prop(self, 'export_type')
        
        if self.export_type == 'COLLECTION':
            flow.prop(self, 'collection_to_export')
        elif self.export_type == 'OBJECT':
            flow.prop(self, 'object_to_export')

    def compute(self, **kwargs):
        depsgraph = bpy.context.evaluated_depsgraph_get()

        stage = self.cached_stage.create()
        UsdGeom.SetStageMetersPerUnit(stage, 1)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)

        root_prim = stage.DefinePrim(f"/{sdf_path(depsgraph.scene.name)}")
        stage.SetDefaultPrim(root_prim)

        objects_prim = stage.DefinePrim(f"{root_prim.GetPath()}/objects")

        if self.export_type == 'SCENE':
            for obj in dg.depsgraph_objects(depsgraph):
                try:
                    object.sync(objects_prim, obj, **kwargs)
                except Exception as e:
                    log.error(e)

        elif self.export_type == 'COLLECTION':
            if self.collection_to_export:
                for obj_col in self.collection_to_export.objects:
                    obj = obj_col.evaluated_get(depsgraph)
                    try:
                        object.sync(objects_prim, obj, **kwargs)
                    except Exception as e:
                        log.error(e)

        elif self.export_type == 'OBJECT':
            if self.object_to_export:
                obj = self.object_to_export.evaluated_get(depsgraph)
                try:
                    object.sync(objects_prim, obj, **kwargs)
                except Exception as e:
                    log.error(e)

        else:
            raise ValueError("Incorrect export_type", self.export_type)

        return stage

    def depsgraph_update(self, depsgraph):
        stage = self.cached_stage()
        if not stage:
            self.final_compute()
            return

        dg.sync_update(stage, depsgraph)
