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

from . import HDUSD_Panel, HdUSD_Operator


def NewListItem(treeList, node):
    item = treeList.add()
    item.name = node.name
    item.nodeIndex = node.selfIndex
    item.childCount = node.childCount
    return item


def SetupListFromNodeData():
    treeList = bpy.context.scene.hdusd.usd_tree
    treeList.clear()

    myNodes = bpy.context.scene.hdusd.myNodes

    for node in myNodes:
        # print("node name:{} parent:{} kids:{}".format(node.name, node.parentIndex, node.children))
        if -1 == node.parentIndex:
            NewListItem(treeList, node)


#
#   Inserts a new item into usd_tree at position item_index
#   by copying data from node
#
def InsertBeneath(treeList, parentIndex, parentIndent, node):
    after_index = parentIndex + 1
    item = NewListItem(treeList, node)
    item.indent = parentIndent + 1
    item_index = len(treeList) - 1  # because add() appends to end.
    treeList.move(item_index, after_index)


def IsChild(child_node_index, parent_node_index, node_list):
    if child_node_index == -1:
        print("bad node index")
        return False

    child = node_list[child_node_index]
    if child.parentIndex == parent_node_index:
        return True
    return False


#
#   Operation to Expand a list item.
#
class UsdTreeItem_Expand(HdUSD_Operator):
    bl_idname = "hdusd.usdtreeitem_expand"
    bl_label = "Tool Name"

    button_id: bpy.props.IntProperty(default=0)

    def execute(self, context):
        item_index = self.button_id
        item_list = context.scene.hdusd.usd_tree
        item = item_list[item_index]
        item_indent = item.indent

        nodeIndex = item.nodeIndex

        myNodes = context.scene.hdusd.myNodes

        print(item)
        if item.expanded:
            print("=== Collapse Item {} ===".format(item_index))
            item.expanded = False

            nextIndex = item_index + 1
            while True:
                if nextIndex >= len(item_list):
                    break
                if item_list[nextIndex].indent <= item_indent:
                    break
                item_list.remove(nextIndex)
        else:
            print("=== Expand Item {} ===".format(item_index))
            item.expanded = True

            for n in myNodes:
                if nodeIndex == n.parentIndex:
                    InsertBeneath(item_list, item_index, item_indent, n)

        return {'FINISHED'}


#
#   Several debug operations
#   (bundled into a single operator with an "action" property)
#
class MyListTreeItem_Debug(bpy.types.Operator):
    bl_idname = "object.mylisttree_debug"
    bl_label = "Debug"

    action: bpy.props.StringProperty(default="default")

    def execute(self, context):
        action = self.action
        if "print" == action:
            print("=== Debug Print ====")
        elif "reset3" == action:
            print("=== Debug Reset ====")
            SetupListFromNodeData()
        elif "clear" == action:
            print("=== Debug Clear ====")
            bpy.context.scene.hdusd.usd_tree.clear()
        else:
            print("unknown debug action: " + action)

        return {'FINISHED'}


class USDTREEITEM_UL_basic(bpy.types.UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        scene = data
        # print(data, item, active_data, active_propname)
        if self.layout_type in {'DEFAULT', 'COMPACT'}:

            for i in range(item.indent):
                split = layout.split(factor=0.1)

            col = layout.column()

            # print("item:{} childCount:{}".format(item.name, item.childCount))
            if item.childCount == 0:
                op = col.operator("hdusd.usdtreeitem_expand", text="", icon='DOT')
                op.button_id = index
                col.enabled = False
            # if False:
            #    pass
            elif item.expanded:
                op = col.operator("hdusd.usdtreeitem_expand", text="", icon='TRIA_DOWN')
                op.button_id = index
            else:
                op = col.operator("hdusd.usdtreeitem_expand", text="", icon='TRIA_RIGHT')
                op.button_id = index

            col = layout.column()
            col.label(text=item.name)


class HDUSD_RENDER_PT_usd(HDUSD_Panel):
    bl_label = "USD Tree"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = "USD"

    @classmethod
    def poll(cls, context):
        return super().poll(context)

    def draw(self, context):
        scene_hdusd = context.scene.hdusd
        layout = self.layout

        row = layout.row()
        row.template_list(
            "USDTREEITEM_UL_basic", "",
            scene_hdusd, "usd_tree",
            scene_hdusd, "usd_tree_index",
            sort_lock=True
        )

        grid = layout.grid_flow(columns=2)

        grid.operator("object.mylisttree_debug", text="Reset").action = "reset3"
        grid.operator("object.mylisttree_debug", text="Clear").action = "clear"
        grid.operator("object.mylisttree_debug", text="Print").action = "print"
