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
from . import HdUSD_Panel, HdUSD_Operator


class HDUSD_MATLIB_OP_import_material(HdUSD_Operator):
    """Import Material"""
    bl_idname = "hdusd.matlib_import_material"
    bl_label = "Import Material"

    def execute(self, context):
        matlib = context.window_manager.hdusd.matlib
        material = matlib.pcoll.materials[matlib.material]
        
        print(material)
        return {"FINISHED"}


class HDUSD_MATLIB_PT_matlib(HdUSD_Panel):
    bl_label = "Material Library"
    bl_context = "material"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        matlib = context.window_manager.hdusd.matlib

        layout.prop(matlib, "category")
        layout.template_icon_view(matlib, "material")

        layout.operator(HDUSD_MATLIB_OP_import_material.bl_idname)

