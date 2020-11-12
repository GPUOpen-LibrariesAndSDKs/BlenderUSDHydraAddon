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
from pxr import Usd


_stage_cache = Usd.StageCache()


class UsdListItem(bpy.types.PropertyGroup):
    sdf_path: bpy.props.StringProperty(name='USD Path', default="")
    expanded: bpy.props.BoolProperty(default=False)

    @property
    def indent(self):
        return self.sdf_path.count('/') - 1


class UsdList(bpy.types.PropertyGroup):
    items: bpy.props.CollectionProperty(type=UsdListItem)
    item_index: bpy.props.IntProperty(default=-1)
    usd_id: bpy.props.IntProperty(default=-1)

    def set_stage(self, stage):
        self.items.clear()
        self.item_index = -1

        if not stage:
            self.usd_id = -1
            return

        self.usd_id = _stage_cache.Insert(stage).ToLongInt()
        for prim in stage.GetPseudoRoot().GetChildren():
            item = self.items.add()
            item.sdf_path = str(prim.GetPath())

    def get_stage(self):
        return _stage_cache.Find(Usd.StageCache.Id.FromLongInt(self.usd_id))

    def clear_stage(self):
        if self.usd_id > 0:
            _stage_cache.Erase(Usd.StageCache.Id.FromLongInt(self.usd_id))

    def get_prim(self, item):
        stage = self.get_stage()
        return stage.GetPrimAtPath(item.sdf_path) if stage else None
