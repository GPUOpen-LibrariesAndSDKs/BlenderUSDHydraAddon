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


def update(usd_tree_name):
    clear()

    if not usd_tree_name:
        return

    output_node = bpy.data.node_groups[usd_tree_name].get_output_node()
    if not output_node:
        return

    stage = output_node.cached_stage()
    if not stage:
        stage = output_node.final_compute('Input')

    if not stage:
        return

    create(stage)


def clear():
    print("clear")
    pass


def create(stage):
    print(stage)
    pass
