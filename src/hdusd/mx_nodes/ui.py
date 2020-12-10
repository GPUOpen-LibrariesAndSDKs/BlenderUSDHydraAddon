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

from ..ui import HdUSD_Panel
from .node_tree import MxNodeTree


class HDUSD_OP_MX_import_material(bpy.types.Operator):
    """Expand USD item"""
    bl_idname = "hdusd.mx_import_material"
    bl_label = "Import Material"

    def execute(self, context):
        return {'FINISHED'}


class HDUSD_MX_MATERIAL_PT_import_export(HdUSD_Panel):
    bl_label = "MaterialX Import/Export"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Tool"

    @classmethod
    def poll(cls, context):
        return isinstance(bpy.context.space_data.edit_tree, MxNodeTree)

    def draw(self, context):
        self.layout.operator('hdusd.mx_import_material')
