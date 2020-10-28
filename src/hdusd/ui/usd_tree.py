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

from . import HdUSD_Panel, HdUSD_Operator


class UsdTreeItem_Expand(HdUSD_Operator):
    """Operation to Expand a list item"""

    bl_idname = "hdusd.usdtreeitem_expand"
    bl_label = "Tool Name"

    index: bpy.props.IntProperty(default=0)

    def execute(self, context):
        usd_tree = context.scene.hdusd.usd_tree
        items = usd_tree.items
        item = items[self.index]

        if item.expanded:
            next_index = self.index + 1
            item_indent = item.indent
            removed_items = 0
            while True:
                if next_index >= len(items):
                    break
                if items[next_index].indent <= item_indent:
                    break
                items.remove(next_index)
                removed_items += 1

            if usd_tree.item_index > self.index:
                usd_tree.item_index = max(self.index, usd_tree.item_index - removed_items)

        else:
            stage, prim = item.get_stage_prim()

            added_items = 0
            for child_index, child_prim in enumerate(prim.GetChildren(), self.index + 1):
                child_item = items.add()
                child_item.sdf_path = str(child_prim.GetPath())
                items.move(len(items) - 1, child_index)
                added_items += 1

            if usd_tree.item_index > self.index:
                usd_tree.item_index += added_items

        item.expanded = not item.expanded

        return {'FINISHED'}


class HDUSD_UL_tree_item(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type not in {'DEFAULT', 'COMPACT'}:
            return

        for i in range(item.indent):
            layout.split(factor=0.1)

        stage, prim = item.get_stage_prim()
        if not prim:
            return

        col = layout.column()
        if not prim.GetChildren():
            icon = 'DOT'
            col.enabled = False
        else:
            icon = 'TRIA_DOWN' if item.expanded else 'TRIA_RIGHT'

        col.operator("hdusd.usdtreeitem_expand", text="", icon=icon).index = index

        col = layout.column()
        col.label(text=prim.GetName())

        col = layout.column()
        col.alignment = 'RIGHT'
        col.label(text=prim.GetTypeName())


class UsdTree_Debug(bpy.types.Operator):
    """Several debug operations"""
    bl_idname = "hdusd.usdtree_debug"
    bl_label = "Debug"

    action: bpy.props.StringProperty(default="default")

    def execute(self, context):
        usd_tree = bpy.context.scene.hdusd.usd_tree
        if self.action == 'print':
            print("=== Debug Print ====")
        elif self.action == 'reload':
            print("=== Debug Reload ====")
            usd_tree.reload()
        elif self.action == 'clear':
            print("=== Debug Clear ====")
            usd_tree.items.clear()
        else:
            raise NotImplemented("Unknown debug action:", self.action)

        return {'FINISHED'}


class HDUSD_RENDER_PT_usd(HdUSD_Panel):
    bl_label = "USD Tree"
    # bl_space_type = "NODE_EDITOR"
    # bl_region_type = "UI"
    # bl_category = "USD"

    def draw(self, context):
        usd_tree = context.scene.hdusd.usd_tree
        layout = self.layout

        # row = layout.row()
        # row.prop(usd_tree, 'usd_file')

        row = layout.row()
        row.template_list(
            "HDUSD_UL_tree_item", "",
            usd_tree, "items",
            usd_tree, "item_index",
            sort_lock=True
        )

        if usd_tree.item_index >= 0:
            item = usd_tree.items[usd_tree.item_index]
            stage, prim = item.get_stage_prim()

            col = layout.column()
            col.label(text=f"Name: {prim.GetName()}")
            col.label(text=f"Path: {prim.GetPath()}")
            col.label(text=f"Type: {prim.GetTypeName()}")
            
        # grid = layout.grid_flow(columns=2)
        # grid.operator("hdusd.usdtree_debug", text="Reload").action = 'reload'
        # grid.operator("hdusd.usdtree_debug", text="Clear").action = 'clear'
        # grid.operator("hdusd.usdtree_debug", text="Print").action = 'print'
