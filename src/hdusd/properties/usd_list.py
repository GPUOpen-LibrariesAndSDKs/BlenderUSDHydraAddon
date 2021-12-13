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
from bpy.types import PropertyGroup
from bpy.props import (
    CollectionProperty,
    StringProperty,
    IntProperty,
    FloatProperty,
    EnumProperty,
    PointerProperty,
)

from . import CachedStageProp
from . import log


class PrimPropertyItem(PropertyGroup):
    def value_float_update(self, context):
        if not self.name:
            # property is not initialized yet
            return

        # TODO: implementation
        pass

    name: StringProperty(name="Name", default="")
    type: EnumProperty(
        items=(('STR', "String", "String value"),
               ('FLOAT', "Float", "Float value")),
        default='STR'
    )
    value_str: StringProperty(name="Value", default="")
    value_float: FloatProperty(name="Float", default=0.0, update=value_float_update)

    def init(self, name, value):
        if isinstance(value, str):
            self.value_str = value
            self.type = 'STR'
        else:
            self.value_float = value
            self.type = 'FLOAT'

        self.name = name


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
            prop.init(name, value)

        add_prop("Name", prim.GetName())
        add_prop("Path", str(prim.GetPath()))
        add_prop("Type", str(prim.GetTypeName()))

    items: CollectionProperty(type=UsdListItem)
    item_index: IntProperty(name="USD Item", default=-1, update=item_index_update)

    prim_properties: CollectionProperty(type=PrimPropertyItem)
    cached_stage: PointerProperty(type=CachedStageProp)

    def update_items(self):
        self.items.clear()
        self.item_index = -1

        stage = self.cached_stage()
        if stage:
            for prim in stage.GetPseudoRoot().GetChildren():
                item = self.items.add()
                item.sdf_path = str(prim.GetPath())

    def get_prim(self, item):
        stage = self.cached_stage()
        return stage.GetPrimAtPath(item.sdf_path) if stage else None

    @property
    def selected_prim(self):
        item = self.items[self.item_index]
        return self.get_prim(item)
