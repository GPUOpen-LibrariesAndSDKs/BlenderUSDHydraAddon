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

from . import HdUSD_Panel
from ..properties.object import GEOM_TYPES


class HDUSD_OP_usd_object_show_hide(bpy.types.Operator):
    """Show/Hide USD object"""
    bl_idname = "hdusd.usd_object_show_hide"
    bl_label = "Show/Hide"

    def execute(self, context):
        obj = context.object
        prim = obj.hdusd.get_prim()
        im = UsdGeom.Imageable(prim)
        if im.ComputeVisibility() == 'invisible':
            im.MakeVisible()
        else:
            im.MakeInvisible()

        return {'FINISHED'}


class HDUSD_OBJECT_PT_usd_settings(HdUSD_Panel):
    bl_label = "USD Settings"
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

        if prim.GetTypeName() in GEOM_TYPES:
            visible = UsdGeom.Imageable(prim).ComputeVisibility() != 'invisible'
            icon = 'HIDE_OFF' if visible else 'HIDE_ON'

            col1.label(text="Visibility")
            col2.operator(HDUSD_OP_usd_object_show_hide.bl_idname,
                          text="Hide" if visible else 'Show',
                          icon='HIDE_OFF' if visible else 'HIDE_ON',
                          emboss=True, depress=False)
