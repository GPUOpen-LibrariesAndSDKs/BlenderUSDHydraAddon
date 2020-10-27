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


class MyListTreeNode(bpy.types.PropertyGroup):
    name: ""
    selfIndex: bpy.props.IntProperty(default=-1)
    parentIndex: bpy.props.IntProperty(default=-1)
    childCount: bpy.props.IntProperty(default=0)


class UsdTreeItem(bpy.types.PropertyGroup):
    indent: bpy.props.IntProperty(default=0)
    expanded: bpy.props.BoolProperty(default=False)
    nodeIndex: bpy.props.IntProperty(default=-1) #index into the real tree data.
    childCount: bpy.props.IntProperty(default=0) #should equal myNodes[nodeIndex].childCount


def SetupNodeData():
    myNodes = bpy.context.scene.hdusd.myNodes
    myNodes.clear()

    for i in range(5):
        node = myNodes.add()
        node.name = "node {}".format(i)
        node.selfIndex = len(myNodes) - 1

    for i in range(4):
        node = myNodes.add()
        node.name = "subnode {}".format(i)
        node.selfIndex = len(myNodes) - 1
        node.parentIndex = 2

    parentIndex = len(myNodes) - 2

    for i in range(2):
        node = myNodes.add()
        node.name = "subnode {}".format(i)
        node.selfIndex = len(myNodes) - 1
        node.parentIndex = parentIndex

    parentIndex = len(myNodes) - 3

    for i in range(2):
        node = myNodes.add()
        node.name = "subnode {}".format(i)
        node.selfIndex = len(myNodes) - 1
        node.parentIndex = parentIndex

    parentIndex = len(myNodes) - 1

    for i in range(2):
        node = myNodes.add()
        node.name = "subnode {}".format(i)
        node.selfIndex = len(myNodes) - 1
        node.parentIndex = parentIndex

    # calculate childCount for all nodes
    for node in myNodes:
        if node.parentIndex != -1:
            parent = myNodes[node.parentIndex]
            parent.childCount = parent.childCount + 1

    print("++++ SetupNodeData ++++")
    print("Node count: {}".format(len(myNodes)))
    for i in range(len(myNodes)):
        node = myNodes[i]
        print("{} node:{} child:{}".format(i, node.name, node.childCount))
