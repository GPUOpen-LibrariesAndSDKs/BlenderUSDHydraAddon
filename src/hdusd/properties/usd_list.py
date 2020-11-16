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
from bpy.types import PropertyGroup
from bpy.props import (
    CollectionProperty,
    StringProperty,
    IntProperty,
    FloatProperty,
)
from pxr import Usd


_stage_cache = Usd.StageCache()


class PrimPropertyItem(PropertyGroup):
    def value_float_update(self, context):
        pass

    name: StringProperty(name='Name', default="")
    type: IntProperty(default=0)
    value_str: StringProperty(name='Str', default="")
    value_float: FloatProperty(name='Float', default=0.0, update=value_float_update)


class UsdListItem(PropertyGroup):
    sdf_path: StringProperty(name='USD Path', default="")

    @property
    def indent(self):
        return self.sdf_path.count('/') - 1


class UsdList(PropertyGroup):
    def item_index_update(self, context):
        self.prim_properties.clear()
        if self.item_index == -1:
            return

        item = self.items[self.item_index]
        prim = self.get_prim(item)

        def add_prop(name, value):
            prop = self.prim_properties.add()
            prop.name = name
            if isinstance(value, str):
                prop.value_str = value
                prop.type = 0
            else:
                prop.value_float = value
                prop.type = 1

        add_prop("Name", prim.GetName())
        add_prop("Path", str(prim.GetPath()))
        add_prop("Type", str(prim.GetTypeName()))
        add_prop('location_x', 0.0)

    items: CollectionProperty(type=UsdListItem)
    item_index: IntProperty(default=-1, update=item_index_update)
    usd_id: IntProperty(default=-1)

    prim_properties: CollectionProperty(type=PrimPropertyItem)

    def set_stage(self, stage):
        self.items.clear()
        self.item_index = -1
        if self.usd_id > 0:
            _stage_cache.Erase(Usd.StageCache.Id.FromLongInt(self.usd_id))
            self.usd_id = -1

        if not stage:
            return

        self.usd_id = _stage_cache.Insert(stage).ToLongInt()
        for prim in stage.GetPseudoRoot().GetChildren():
            item = self.items.add()
            item.sdf_path = str(prim.GetPath())

    def get_stage(self):
        return _stage_cache.Find(Usd.StageCache.Id.FromLongInt(self.usd_id))

    def get_prim(self, item):
        stage = self.get_stage()
        return stage.GetPrimAtPath(item.sdf_path) if stage else None
