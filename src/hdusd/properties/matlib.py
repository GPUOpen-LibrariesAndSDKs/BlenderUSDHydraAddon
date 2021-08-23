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

from . import HdUSDProperties

from ..utils import matlib


class MatlibProperties(bpy.types.PropertyGroup):
    pcoll = None

    def get_materials(self, context):
        if self.pcoll.materials is not None:
            return self.pcoll.materials

        self.pcoll.materials = []
        for i, mat in enumerate(matlib.Material.get_all_materials()):
            render = mat.renders[0]
            render.get_info()
            render.get_thumbnail()

            thumbnail = self.pcoll.load(render.thumbnail, str(render.thumbnail_path), 'IMAGE')
            description = f"{mat.title}"
            if mat.description:
                description += f"\n{mat.description}"
            description += f"\nAuthor: {mat.author}"
            self.pcoll.materials.append((mat.id, mat.title, description, thumbnail.icon_id, i))

        return self.pcoll.materials

    materials: bpy.props.EnumProperty(
        name="Materials",
        items=get_materials
    )

    @classmethod
    def register(cls):
        import bpy.utils.previews
        cls.pcoll = bpy.utils.previews.new()
        cls.pcoll.materials = None

    @classmethod
    def unregister(cls):
        bpy.utils.previews.remove(cls.pcoll)


class WindowManagerProperties(HdUSDProperties):
    bl_type = bpy.types.WindowManager

    matlib: bpy.props.PointerProperty(type=MatlibProperties)
