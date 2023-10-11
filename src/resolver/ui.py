# **********************************************************************
# Copyright 2023 Advanced Micro Devices, Inc
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


class RS_RESOLVER_PT_resolver(bpy.types.Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'render'
    bl_label = "RenderStudio Resolver"

    def draw(self, context):
        from .resolver import rs_resolver
        layout = self.layout
        if rs_resolver.is_connected:
            layout.operator("resolver.disconnect", icon='UNLINKED')

        else:
            layout.operator("resolver.connect", icon='LINKED')

        layout.separator()
        layout.operator("resolver.export_stage")

def draw_button(self, context):
    from .resolver import rs_resolver
    if rs_resolver.is_connected:
        self.layout.operator("resolver.disconnect", icon='UNLINKED')

    else:
        self.layout.operator("resolver.connect", icon='LINKED')


def register():
    bpy.utils.register_class(RS_RESOLVER_PT_resolver)
    bpy.types.OUTLINER_HT_header.prepend(draw_button)


def unregister():
    bpy.types.OUTLINER_HT_header.remove(draw_button)
    bpy.utils.unregister_class(RS_RESOLVER_PT_resolver)
