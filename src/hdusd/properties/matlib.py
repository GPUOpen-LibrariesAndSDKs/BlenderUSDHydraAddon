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

    def _set_materials(self):
        self.pcoll.materials = {}
        for mat in matlib.Material.get_all_materials():
            render = mat.renders[0]
            render.get_info()
            render.get_thumbnail()
            render.thumbnail_load(self.pcoll)

            if mat.category:
                mat.category.get_info()

            self.pcoll.materials[mat.id] = mat

    def get_materials(self, context):
        if self.pcoll.materials is None:
            self._set_materials()

        materials = []
        for i, mat in enumerate(self.pcoll.materials.values()):
            if self.category != 'NONE' and mat.category and mat.category.id != self.category:
                continue

            description = f"{mat.title}"
            if mat.description:
                description += f"\n{mat.description}"
            if mat.category:
                description += f"\nCategory: {mat.category.title}"
            description += f"\nAuthor: {mat.author}"

            materials.append((mat.id, mat.title, description,mat.renders[0].thumbnail_icon_id, i))

        return materials

    def _set_categories(self):
        self.pcoll.categories = {}
        for mat in matlib.Material.get_all_materials():
            cat = mat.category
            if not cat or cat.id in self.pcoll.categories:
                continue

            cat.get_info()
            self.pcoll.categories[cat.id] = cat

    def get_categories(self, context):
        if self.pcoll.categories is None:
            self._set_categories()

        categories = [(cat.id, cat.title, f"Category: {cat.title}")
                      for cat in self.pcoll.categories.values()]
        categories.insert(0, ('NONE', "", "No category"))
        return categories

    material: bpy.props.EnumProperty(
        name="Material",
        description="Select material",
        items=get_materials
    )

    category: bpy.props.EnumProperty(
        name="Category",
        description="Select materials category",
        items=get_categories
    )

    @classmethod
    def register(cls):
        import bpy.utils.previews
        cls.pcoll = bpy.utils.previews.new()
        cls.pcoll.materials = None
        cls.pcoll.categories = None

    @classmethod
    def unregister(cls):
        bpy.utils.previews.remove(cls.pcoll)


class WindowManagerProperties(HdUSDProperties):
    bl_type = bpy.types.WindowManager

    matlib: bpy.props.PointerProperty(type=MatlibProperties)
