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

from pxr import UsdGeom

from . import HdUSD_Panel, HdUSD_Operator
from ..usd_nodes.nodes.base_node import USDNode


class HDUSD_OP_usd_list_item_expand(HdUSD_Operator):
    """Operation to Expand a list item"""
    bl_idname = "hdusd.usd_list_item_expand"
    bl_description = "Expand USD item"

    index: bpy.props.IntProperty(default=-1)

    def execute(self, context):
        if self.index == -1:
            return {'CANCELLED'}

        node = context.active_node
        usd_list = node.hdusd.usd_list
        items = usd_list.items
        item = items[self.index]

        if len(items) > self.index + 1 and items[self.index + 1].indent > item.indent:
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

        return {'FINISHED'}


class HDUSD_OP_usd_list_item_show_hide(HdUSD_Operator):
    """Operation to change show/hide USD item"""
    bl_idname = "hdusd.usd_list_item_show_hide"
    bl_description = "Show/Hide USD item"

    index: bpy.props.IntProperty(default=-1)

    def execute(self, context):
        if self.index == -1:
            return {'CANCELLED'}

        node = context.active_node
        usd_list = node.hdusd.usd_list
        items = usd_list.items
        item = items[self.index]

        prim = usd_list.get_prim(item)
        im = UsdGeom.Imageable(prim)
        if im.ComputeVisibility() == 'invisible':
            im.MakeVisible()
        else:
            im.MakeInvisible()

        return {'FINISHED'}


class HDUSD_UL_usd_list_item(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type not in {'DEFAULT', 'COMPACT'}:
            return

        for i in range(item.indent):
            layout.split(factor=0.1)

        items = data.items
        prim = data.get_prim(item)
        if not prim:
            return

        visible = UsdGeom.Imageable(prim).ComputeVisibility() != 'invisible'

        col = layout.column()
        if not prim.GetChildren():
            icon = 'DOT'
            col.enabled = False
        elif len(items) > index + 1 and items[index + 1].indent > item.indent:
            icon = 'TRIA_DOWN'
        else:
            icon = 'TRIA_RIGHT'

        expand_op = col.operator("hdusd.usd_list_item_expand", text="", icon=icon,
                                 emboss=False, depress=False)
        expand_op.index = index

        col = layout.column()
        col.label(text=prim.GetName())
        col.enabled = visible

        col = layout.column()
        col.alignment = 'RIGHT'
        col.label(text=prim.GetTypeName())
        col.enabled = visible

        col = layout.column()
        col.alignment = 'RIGHT'
        if prim.GetTypeName() == 'Xform':
            icon = 'HIDE_OFF' if visible else 'HIDE_ON'
        else:
            col.enabled = False
            icon = 'NONE'

        visible_op = col.operator("hdusd.usd_list_item_show_hide", text="", icon=icon,
                                  emboss=False, depress=False)
        visible_op.index = index


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

        layout.template_list(
            "HDUSD_UL_usd_list_item", "",
            usd_list, "items",
            usd_list, "item_index",
            sort_lock=True
        )

        prop_layout = layout.column()
        prop_layout.use_property_split = True
        for prop in usd_list.prim_properties:
            if prop.type == 'str' and prop.value_str:
                row = prop_layout.row()
                row.enabled = False
                row.prop(prop, 'value_str', text=prop.name)
            elif prop.type == 'float':
                prop_layout.prop(prop, 'value_float', text=prop.name)
