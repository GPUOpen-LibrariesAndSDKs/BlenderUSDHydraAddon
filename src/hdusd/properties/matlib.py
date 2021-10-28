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

from ..utils import logging
log = logging.Log(tag='properties.matlib')


thread_pool = futures.ThreadPoolExecutor()
mutex = threading.Lock()


class MatlibProperties(bpy.types.PropertyGroup):
    @classmethod
    def load_data(cls):
        cls.pcoll.materials = {}
        cls.pcoll.categories = {}

        def category_load(cat):
            cat.get_info()
            cls.pcoll.categories[cat.id] = cat

        def material_load(mat):
            for render in mat.renders:
                render.get_info()
                render.get_thumbnail()
                render.thumbnail_load(cls.pcoll)

            for package in mat.packages:
                package.get_info()

            cls.pcoll.materials[mat.id] = mat

        def load():
            with futures.ThreadPoolExecutor() as executor:
                # getting cached materials
                materials = {mat.id: mat for mat in matlib.Material.get_materials_cache()}
                categories = {mat.category.id: mat.category for mat in materials.values()}

                category_loaders = [executor.submit(category_load, cat)
                                    for cat in categories.values()]
                for _ in futures.as_completed(category_loaders):
                    pass

                for mat in materials.values():
                    mat.category.get_info()

                material_loaders = [executor.submit(material_load, mat)
                                    for mat in materials.values()]
                for _ in futures.as_completed(material_loaders):
                    pass

                # getting and syncing with online materials
                online_materials = {mat.id: mat for mat in matlib.Material.get_materials()}
                new_material_ids = online_materials.keys() - materials.keys()
                new_materials = {mat_id: online_materials[mat_id] for mat_id in new_material_ids}

                new_categories = {}
                for mat in new_materials.values():
                    cat = mat.category
                    if cat.id not in categories and cat.id not in new_categories:
                        new_categories[cat.id] = cat

                category_loaders = [executor.submit(category_load, cat)
                                    for cat in new_categories.values()]
                for _ in futures.as_completed(category_loaders):
                    pass

                for mat in new_materials.values():
                    mat.category.get_info()

                material_loaders = [executor.submit(material_load, mat)
                                    for mat in new_materials.values()]
                for _ in futures.as_completed(material_loaders):
                    pass

        cls.load_thread = threading.Thread(target=load)
        cls.load_thread.start()

    def get_materials(self) -> dict:
        materials = {}
        search_str = self.search.strip().lower()

        # converting to list in thread safe purposes
        materials_list = list(self.pcoll.materials.values())

        for mat in materials_list:
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

        # converting to list in thread safe purposes
        categories_list = list(self.pcoll.categories.values())

        categories += ((cat.id, cat.title, f"Show materials with category {cat.title}")
                       for cat in categories_list)
        return categories

    def get_packages_prop(self, context):
        mat = self.pcoll.materials.get(self.material_id)
        if not mat:
            return []

        return [(p.id, f"{p.label} ({p.size})", "")
                for p in sorted(mat.packages)]

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
        cls.load_thread = None
        cls.status = ""

    @classmethod
    def unregister(cls):
        bpy.utils.previews.remove(cls.pcoll)


class WindowManagerProperties(HdUSDProperties):
    bl_type = bpy.types.WindowManager

    matlib: bpy.props.PointerProperty(type=MatlibProperties)
