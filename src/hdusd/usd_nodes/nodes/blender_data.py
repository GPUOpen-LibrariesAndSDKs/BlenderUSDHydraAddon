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
from ...export import object, material, world
from ...utils import depsgraph_objects


#
# COLLECTION MENU and OPERATORS
#
class HDUSD_USD_NODETREE_OP_blender_data_link_collection(bpy.types.Operator):
    """Link collection"""
    bl_idname = "hdusd.usd_nodetree_blender_data_link_collection"
    bl_label = ""

    collection_name: bpy.props.StringProperty(default="")

    def execute(self, context):
        context.node.collection = bpy.data.collections[self.collection_name]
        return {"FINISHED"}


class HDUSD_USD_NODETREE_OP_blender_data_unlink_collection(bpy.types.Operator):
    """Unlink collection"""
    bl_idname = "hdusd.usd_nodetree_blender_data_unlink_collection"
    bl_label = ""

    def execute(self, context):
        context.node.collection = None
        return {"FINISHED"}


class HDUSD_USD_NODETREE_MT_blender_data_collection(bpy.types.Menu):
    bl_idname = "HDUSD_USD_NODETREE_MT_blender_data_collection"
    bl_label = "Object"

    def draw(self, context):
        layout = self.layout
        collections = bpy.data.collections

        for coll in collections:
            if coll.name == "USD NodeTree":
                continue

            row = layout.row()
            op = row.operator(HDUSD_USD_NODETREE_OP_blender_data_link_collection.bl_idname,
                              text=coll.name)
            op.collection_name = coll.name


#
# OBJECT MENU and OPERATORS
#
class HDUSD_USD_NODETREE_OP_blender_data_link_object(bpy.types.Operator):
    """Link object"""
    bl_idname = "hdusd.usd_nodetree_blender_data_link_object"
    bl_label = ""

    object_name: bpy.props.StringProperty(default="")

    def execute(self, context):
        context.node.object = bpy.data.objects[self.object_name]
        return {"FINISHED"}


class HDUSD_USD_NODETREE_OP_blender_data_unlink_object(bpy.types.Operator):
    """Unlink object"""
    bl_idname = "hdusd.usd_nodetree_blender_data_unlink_object"
    bl_label = ""

    def execute(self, context):
        context.node.object = None
        return {"FINISHED"}


class HDUSD_USD_NODETREE_MT_blender_data_object(bpy.types.Menu):
    bl_idname = "HDUSD_USD_NODETREE_MT_blender_data_object"
    bl_label = "Object"

    def draw(self, context):
        layout = self.layout
        objects = bpy.data.objects

        for obj in objects:
            if obj.hdusd.is_usd:
                continue

            row = layout.row()
            op = row.operator(HDUSD_USD_NODETREE_OP_blender_data_link_object.bl_idname,
                              text=obj.name)
            op.object_name = obj.name


class BlenderDataNode(USDNode):
    """Blender data to USD can export whole scene, one collection or object"""
    bl_idname = 'usd.BlenderDataNode'
    bl_label = "Blender Data"

    input_names = ()
    use_hard_reset = False

    def update_data(self, context):
        self.reset(True)

    data: bpy.props.EnumProperty(
        name="Data",
        description="Blender Data to read",
        items=(('SCENE', "Scene", "Read entire scene"),
            ('COLLECTION', "Collection", "Read collection"),
            ('OBJECT', 'Object', "Read single object"),
        ),
        default='SCENE',
        update=update_data
    )
    collection: bpy.props.PointerProperty(
        type=bpy.types.Collection,
        name="Collection",
        description="",
        update=update_data
    )
    object: bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="Object",
        description="",
        update=update_data
    )

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        col.prop(self, 'data')

        if self.data == 'COLLECTION':
            split = layout.row(align=True).split(factor=0.25)
            col = split.column()
            col.label(text="Collection")
            col = split.column()
            row = col.row(align=True)
            if self.collection:
                row.menu(HDUSD_USD_NODETREE_MT_blender_data_collection.bl_idname,
                         text=self.collection.name, icon='OUTLINER_COLLECTION')
                row.operator(HDUSD_USD_NODETREE_OP_blender_data_unlink_collection.bl_idname, icon='X')
            else:
                row.menu(HDUSD_USD_NODETREE_MT_blender_data_collection.bl_idname,
                         text=" ", icon='OUTLINER_COLLECTION')

        elif self.data == 'OBJECT':
            split = layout.row(align=True).split(factor=0.25)
            col = split.column()
            col.label(text="Object")
            col = split.column()
            row = col.row(align=True)
            if self.object:
                row.menu(HDUSD_USD_NODETREE_MT_blender_data_object.bl_idname,
                         text=self.object.name, icon='OBJECT_DATAMODE')
                row.operator(HDUSD_USD_NODETREE_OP_blender_data_unlink_object.bl_idname, icon='X')
            else:
                row.menu(HDUSD_USD_NODETREE_MT_blender_data_object.bl_idname,
                         text=" ", icon='OBJECT_DATAMODE')

    def compute(self, **kwargs):
        depsgraph = bpy.context.evaluated_depsgraph_get()

        stage = self.cached_stage.create()
        UsdGeom.SetStageMetersPerUnit(stage, 1)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)

        root_prim = stage.GetPseudoRoot()

        if self.data == 'SCENE':
            for obj in depsgraph_objects(depsgraph):
                object.sync(root_prim, obj)

            world.sync(root_prim, depsgraph.scene.world)

        elif self.data == 'COLLECTION':
            if not self.collection:
                return

            for obj_col in self.collection.objects:
                if obj_col.hdusd.is_usd:
                    continue

                object.sync(root_prim, obj_col.evaluated_get(depsgraph))

        elif self.data == 'OBJECT':
            if not self.object or self.object.hdusd.is_usd:
                return

            object.sync(root_prim, self.object.evaluated_get(depsgraph))

        return stage

    def depsgraph_update(self, depsgraph):
        stage = self.cached_stage()
        if not stage:
            self.final_compute()
            return

        is_updated = False

        root_prim = stage.GetPseudoRoot()

        for update in depsgraph.updates:
            if isinstance(update.id, bpy.types.Scene):
                scene = update.id
                for prim in root_prim.GetAllChildren():
                    vsets = prim.GetVariantSets()
                    if 'delegate' not in vsets.GetNames():
                        continue

                    vset = vsets.GetVariantSet('delegate')
                    vset.SetVariantSelection('GL' if scene.hdusd.viewport.is_gl_delegate else 'RPR')

                continue

            if isinstance(update.id, bpy.types.Object):
                obj = update.id
                if obj.hdusd.is_usd:
                    continue

                # checking if object has to be updated
                if self.data == 'COLLECTION':
                    if not self.collection or \
                            obj.name not in self.collection.objects:
                        continue

                elif self.data == 'OBJECT':
                    if not self.object or \
                            object.sdf_name(self.object) != object.sdf_name(obj):
                        continue

                # updating object
                object.sync_update(root_prim, obj,
                                   update.is_updated_geometry, update.is_updated_transform)

                is_updated = True
                continue

            if isinstance(update.id, bpy.types.World):
                if self.data != 'SCENE':
                    continue

                wld = update.id
                world.sync_update(root_prim, wld)

                is_updated = True
                continue

            if isinstance(update.id, bpy.types.Collection):
                coll = update.id

                current_keys = set(prim.GetName() for prim in root_prim.GetAllChildren())
                required_keys = set()
                depsgraph_keys = set(object.sdf_name(obj)
                                     for obj in depsgraph_objects(depsgraph))

                if self.data == 'SCENE':
                    required_keys = depsgraph_keys

                elif self.data == 'COLLECTION':
                    if not self.collection:
                        continue

                    if coll.name != self.collection.name:
                        continue

                    required_keys = set(object.sdf_name(obj) for obj in coll.objects)
                    required_keys.intersection_update(depsgraph_keys)

                elif self.data == 'OBJECT':
                    if not self.object:
                        continue

                    if object.sdf_name(self.object) in depsgraph_keys:
                        required_keys = {object.sdf_name(self.object)}

                keys_to_remove = current_keys - required_keys
                keys_to_add = required_keys - current_keys

                if keys_to_remove:
                    for key in keys_to_remove:
                        root_prim.GetStage().RemovePrim(root_prim.GetPath().AppendChild(key))

                    is_updated = True

                if keys_to_add:
                    for obj in depsgraph_objects(depsgraph):
                        obj_key = object.sdf_name(obj)
                        if obj_key not in keys_to_add:
                            continue

                        object.sync(root_prim, obj)

                    is_updated = True

                continue

        if is_updated:
            self.hdusd.usd_list.update_items()
            self._reset_next(True)

    def material_update(self, mat):
        stage = self.cached_stage()
        material.sync_update_all(stage.GetPseudoRoot(), mat)
