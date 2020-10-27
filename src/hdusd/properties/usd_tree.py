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


class UsdTreeItem(bpy.types.PropertyGroup):
    sdf_path: bpy.props.StringProperty(name='USD Path', default="")
    expanded: bpy.props.BoolProperty(default=False)

    @property
    def indent(self):
        return self.sdf_path.count('/') - 1

    @property
    def child_count(self):
        stage, prim = self.get_stage_prim()
        return len(prim.GetChildren())

    @property
    def prim_name(self):
        stage, prim = self.get_stage_prim()
        return prim.GetName()

    def get_stage_prim(self):
        stage = bpy.context.scene.hdusd.usd_tree.get_stage()
        prim = stage.GetPrimAtPath(self.sdf_path)
        return stage, prim


class UsdTree(bpy.types.PropertyGroup):
    items: bpy.props.CollectionProperty(type=UsdTreeItem)
    item_index: bpy.props.IntProperty()
    usd_file: bpy.props.StringProperty(name="USD File", subtype='FILE_PATH')

    def get_stage(self):
        return Usd.Stage.Open(self.usd_file)

    def reload(self):
        self.items.clear()
        self.item_index = -1
        stage = self.get_stage()
        root = stage.GetPseudoRoot()
        for prim in root.GetChildren():
            item = self.items.add()
            item.sdf_path = str(prim.GetPath())
