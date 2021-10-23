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
from concurrent import futures

import bpy

from . import HdUSDProperties

from ..utils import matlib


class MatlibProperties(bpy.types.PropertyGroup):
    pcoll = None

    def _set_materials(self):
        self.pcoll.materials = {}
        materials = list(matlib.Material.get_all_materials())
        for mat in materials:
            if mat.category:
                mat.category.get_info()

        def render_load(mat):
            render = mat.renders[0]
            render.get_info()
            render.get_thumbnail()
            render.thumbnail_load(self.pcoll)

        with futures.ThreadPoolExecutor(max_workers=5) as executor:
            fs = {executor.submit(render_load, mat): mat for mat in materials}
            for f in futures.as_completed(fs):
                mat = fs[f]
                self.pcoll.materials[mat.id] = mat

    def get_materials(self, context):
        if not self.pcoll.materials:
            self._set_materials()

        materials = []
        if not self.pcoll.materials:
            return materials

        search_string = self.search.strip().lower()
        for i, mat in enumerate(self.pcoll.materials.values()):
            if self.category != 'ALL' and (not mat.category or mat.category.id != self.category):
                continue

            if search_string and not search_string in mat.title.strip().lower():
                continue

            description = f"{mat.title}"
            if mat.description:
                description += f"\n{mat.description}"
            if mat.category:
                description += f"\nCategory: {mat.category.title}"
            description += f"\nAuthor: {mat.author}"

            materials.append((mat.id, mat.title, description, mat.renders[0].thumbnail_icon_id, i))

        return materials

    def _set_categories(self):
        self.pcoll.categories = {}

        if not self.pcoll.materials:
            self._set_materials()

        for mat in self.pcoll.materials:
            cat = self.pcoll.materials[mat].category
            if not cat or cat.id in self.pcoll.categories:
                continue

            cat.get_info()
            self.pcoll.categories[cat.id] = cat

    def get_categories(self, context):
        if self.pcoll.categories is None:
            self._set_categories()

        categories = [('ALL', "All Categories", "Show materials for all categories")]
        categories += ((cat.id, cat.title, f"Category: {cat.title}")
                       for cat in self.pcoll.categories.values())
        return categories

    def update_material(self, context):
        materials = self.get_materials(context)
        if materials and not self.material in [mat[0] for mat in materials]:
            self.material = materials[0][0]
            self.package_id = self.pcoll.materials[self.material].packages[0].id

    material: bpy.props.EnumProperty(
        name="Material",
        description="Select material",
        items=get_materials,
    )
    category: bpy.props.EnumProperty(
        name="Category",
        description="Select materials category",
        items=get_categories,
        update=update_material,
    )
    search: bpy.props.StringProperty(
        name="Search",
        description="Search materials by title",
        update=update_material,
    )
    package_id: bpy.props.StringProperty(
        name="Package id",
        description="Selected material package"
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
