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
from pathlib import Path
import bpy
from pxr import Usd


class UsdTreeItem(bpy.types.PropertyGroup):
    sdf_path: bpy.props.StringProperty(name='USD Path', default="")
    expanded: bpy.props.BoolProperty(default=False)

    @property
    def indent(self):
        return self.sdf_path.count('/') - 1

    def get_stage_prim(self):
        stage = bpy.context.scene.hdusd.usd_tree.get_stage()
        prim = stage.GetPrimAtPath(self.sdf_path) if stage else None
        return stage, prim


class UsdTree(bpy.types.PropertyGroup):
    def update_usd_file(self, context):
        self.reload()

    items: bpy.props.CollectionProperty(type=UsdTreeItem)
    item_index: bpy.props.IntProperty()
    usd_file: bpy.props.StringProperty(
        name="USD File",
        subtype='FILE_PATH',
        update=update_usd_file,
    )

    def get_stage(self):
        if not self.usd_file or not Path(self.usd_file).exists():
            return None

        return Usd.Stage.Open(self.usd_file)

    def reload(self):
        self.items.clear()
        self.item_index = -1

        stage = self.get_stage()
        if not stage:
            return

        root = stage.GetPseudoRoot()
        for prim in root.GetChildren():
            item = self.items.add()
            item.sdf_path = str(prim.GetPath())
