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
from ..usd_nodes.nodes.base_node import USDNode


class HDUSD_OP_usd_list_item_expand(HdUSD_Operator):
    """Operation to Expand a list item"""
    bl_idname = "hdusd.usd_list_item_expand"
    index: bpy.props.IntProperty(default=0)

    def execute(self, context):
        node = context.active_node
        usd_list = node.hdusd.usd_list
        items = usd_list.items
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

            if usd_list.item_index > self.index:
                usd_list.item_index = max(self.index, usd_list.item_index - removed_items)

        else:
            prim = usd_list.get_prim(item)

            added_items = 0
            for child_index, child_prim in enumerate(prim.GetChildren(), self.index + 1):
                child_item = items.add()
                child_item.sdf_path = str(child_prim.GetPath())
                items.move(len(items) - 1, child_index)
                added_items += 1

            if usd_list.item_index > self.index:
                usd_list.item_index += added_items

        item.expanded = not item.expanded

        return {'FINISHED'}


class HDUSD_UL_usd_list_item(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type not in {'DEFAULT', 'COMPACT'}:
            return

        for i in range(item.indent):
            layout.split(factor=0.1)

        prim = data.get_prim(item)
        if not prim:
            return

        col = layout.column()
        if not prim.GetChildren():
            icon = 'DOT'
            col.enabled = False
        else:
            icon = 'TRIA_DOWN' if item.expanded else 'TRIA_RIGHT'

        expand_op = col.operator("hdusd.usd_list_item_expand", text="", icon=icon)
        expand_op.index = index

        col = layout.column()
        col.label(text=prim.GetName())

        col = layout.column()
        col.alignment = 'RIGHT'
        col.label(text=prim.GetTypeName())


def draw_usd_list(usd_list, layout):
    col = layout.column()
    col.template_list(
        "HDUSD_UL_usd_list_item", "",
        usd_list, "items",
        usd_list, "item_index",
        sort_lock=True
    )

    if usd_list.item_index >= 0:
        item = usd_list.items[usd_list.item_index]
        prim = usd_list.get_prim(item)

        col.label(text=f"Name: {prim.GetName()}")
        col.label(text=f"Path: {prim.GetPath()}")
        col.label(text=f"Type: {prim.GetTypeName()}")


class HDUSD_NODE_PT_usd_list(HdUSD_Panel):
    bl_label = "USD List"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Tool"

    @classmethod
    def poll(cls, context):
        node = context.active_node
        return node and isinstance(node, USDNode)

    def draw(self, context):
        node = context.active_node
        usd_list = node.hdusd.usd_list
        layout = self.layout

        draw_usd_list(usd_list, layout)


class HDUSD_OP_usd_nodetree_add_basic_nodes(HdUSD_Operator):
    bl_idname = "hdusd.usd_nodetree_add_basic_nodes"

    scene_source: bpy.props.EnumProperty(
        items=(
            ('SCENE', 'Scene', 'Render current scene'),
            ('USD_FILE', 'USD File', 'Load and render scene from USD file'),
        ),
        default='SCENE',
    )

    def execute(self, context):
        tree = context.space_data.edit_tree
        tree.add_basic_nodes(self.scene_source)
        return {'FINISHED'}


class HDUSD_NODE_PT_node_tree_operations(HdUSD_Panel):
    bl_label = "Setup basic USD Node Tree"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Tool"

    @classmethod
    def poll(cls, context):
        tree = context.space_data.edit_tree
        return super().poll(context) and tree and tree.bl_idname == "hdusd.USDTree"

    def draw(self, context):
        col = self.layout.column()
        col.label(text="Replace current tree using")

        add_scene_nodes_op = col.operator("hdusd.usd_nodetree_add_basic_nodes", text="Current scene")
        add_scene_nodes_op.scene_source = "SCENE"

        add_file_nodes_op = col.operator("hdusd.usd_nodetree_add_basic_nodes", text="USD file")
        add_file_nodes_op.scene_source = "USD_FILE"

