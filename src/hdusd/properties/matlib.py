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
import threading

import bpy

from . import HdUSDProperties

from ..utils import matlib


thread_pool = futures.ThreadPoolExecutor()
mutex = threading.Lock()


class MatlibProperties(bpy.types.PropertyGroup):
    def load_data(self):
        self.pcoll.materials = {}
        self.pcoll.categories = {}

        def load():
            materials = list(matlib.Material.get_all_materials())
            categories = {mat.category.id: mat.category for mat in materials}

            def category_load(cat):
                cat.get_info()
                self.pcoll.categories[cat.id] = cat

            def material_load(mat):
                for render in mat.renders:
                    render.get_info()
                    render.get_thumbnail()
                    render.thumbnail_load(self.pcoll)

                for package in mat.packages:
                    package.get_info()

                self.pcoll.materials[mat.id] = mat

            category_loaders = [self.thread_pool.submit(category_load, cat)
                                for cat in categories.values()]
            for _ in futures.as_completed(category_loaders):
                pass

            for mat in materials:
                mat.category.get_info()

            material_loaders = [self.thread_pool.submit(material_load, mat) for mat in materials]
            for _ in futures.as_completed(material_loaders):
                pass

        self.load_thread = threading.Thread(target=load)
        self.load_thread.start()

    def get_materials(self) -> dict:
        materials = {}
        if self.pcoll.materials is None:
            self.load_data()

        search_str = self.search.strip().lower()
        for mat in self.pcoll.materials.values():
            if search_str not in mat.title.lower():
                continue

            if not (mat.category.id == self.category_id or self.category_id == 'ALL' or
                    (self.category_id == 'NONE' and mat.category.id == '')):
                continue

            materials[mat.id] = mat

        return materials

    def get_materials_prop(self, context):
        return [(mat.id, mat.title, mat.full_description,
                 mat.renders[0].thumbnail_icon_id if mat.renders else 'MATERIAL', i)
                for i, mat in enumerate(self.get_materials().values())]

    def get_categories_prop(self, context):
        categories = []
        if self.pcoll.categories is None:
            return categories

        categories += [('ALL', "All Categories", "Show materials for all categories")]
        if '' in self.pcoll.categories:
            categories += [('NONE', "No Category", "Show materials without category")]

        categories += ((cat.id, cat.title, f"Show materials with category {cat.title}")
                       for cat in self.pcoll.categories.values())
        return categories

    def get_packages_prop(self, context):
        mat = self.pcoll.materials.get(self.material_id)
        if not mat:
            return []

        return [(p.id, f"{p.label} ({p.size})", "")
                for p in mat.packages]

    def update_filter(self, context):
        materials = self.get_materials()
        if materials and self.material_id not in materials:
            self.material_id = next(iter(materials))
            self.package_id = materials[self.material_id].packages[0].id

    material_id: bpy.props.EnumProperty(
        name="Material",
        description="Select material",
        items=get_materials_prop,
    )
    category_id: bpy.props.EnumProperty(
        name="Category",
        description="Select materials category",
        items=get_categories_prop,
        update=update_filter,
    )
    search: bpy.props.StringProperty(
        name="Search",
        description="Search materials by title",
        update=update_filter,
    )
    package_id: bpy.props.EnumProperty(
        name="Package",
        description="Selected material package",
        items=get_packages_prop,
    )

    @classmethod
    def register(cls):
        import bpy.utils.previews
        cls.pcoll = bpy.utils.previews.new()
        cls.pcoll.materials = None
        cls.pcoll.categories = None

        # threading fields
        cls.thread_pool = futures.ThreadPoolExecutor()
        cls.load_thread = None
        cls.status = ""

    @classmethod
    def unregister(cls):
        bpy.utils.previews.remove(cls.pcoll)


class WindowManagerProperties(HdUSDProperties):
    bl_type = bpy.types.WindowManager

    matlib: bpy.props.PointerProperty(type=MatlibProperties)
