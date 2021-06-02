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
    bl_label = "USD Settings"
    bl_context = 'object'

    @classmethod
    def poll(cls, context):
        return super().poll(context) and context.object and context.object.hdusd.is_usd

    def draw(self, context):
        self.layout.use_property_split = True
        self.layout.use_property_decorate = False

        obj = context.object
        col = self.layout.column()
        col.enabled = False
        col.prop(obj.hdusd, 'sdf_path', text="USD Path")
