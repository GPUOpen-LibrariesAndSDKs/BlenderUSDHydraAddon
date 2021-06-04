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
from . import HdUSD_Panel


class HDUSD_OBJECT_PT_usd_settings(HdUSD_Panel):
    bl_label = "USD Prim Settings"
    bl_context = 'object'

    @classmethod
    def poll(cls, context):
        return super().poll(context) and context.object and context.object.hdusd.is_usd

    def draw(self, context):
        obj = context.object
        prim = obj.hdusd.get_prim()
        if not prim:
            return

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        split = layout.row(align=True).split(factor=0.4)
        col1 = split.column()
        col1.alignment = 'RIGHT'
        col2 = split.column()

        col1.label(text="Name")
        col2.label(text=prim.GetName())

        col1.label(text="Path")
        col2.label(text=str(prim.GetPath()))

        col1.label(text="Type")
        col2.label(text=prim.GetTypeName())
