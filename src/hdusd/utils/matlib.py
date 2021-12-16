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
import requests
import weakref
from dataclasses import dataclass, field
import shutil
from pathlib import Path
import zipfile
import json
import threading
from concurrent import futures

import bpy.utils.previews

from . import LIBS_DIR

from ..utils import logging, update_ui
log = logging.Log('utils.matlib')

URL = "https://api.matlib.gpuopen.com/api"
MATLIB_DIR = LIBS_DIR.parent / "matlib"


def download_file(url, path, cache_check=True):
    if cache_check and path.is_file():
        return path

    log("download_file", f"{url=}, {path=}")

    path.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True) as response:
        with open(path, 'wb') as f:
            shutil.copyfileobj(response.raw, f)

    log("download_file", "done")
    return path


def download_file_callback(url, path, update_callback, cache_check=True):
    if cache_check and path.is_file():
        return None

    log("download_file_callback", f"{url=}, {path=}")

    path.parent.mkdir(parents=True, exist_ok=True)
    path_raw = path.with_suffix(".raw")

    size = 0
    with requests.get(url, stream=True) as response:
        with open(path_raw, 'wb') as f:
            if update_callback:
                for chunk in response.iter_content(chunk_size=8192):
                    size += len(chunk)
                    update_callback(size)
                    f.write(chunk)

    path_raw.rename(path)
    log("download_file_callback", "done")
    return path


def request_json(url, params, path, cache_check=True):
    if cache_check and path and path.is_file():
        with open(path) as json_file:
            return json.load(json_file)

    log("request_json", f"{url=}, {params=}, {path=}")

    response = requests.get(url, params=params)
    res_json = response.json()

    if path:
        save_json(res_json, path)

    log("request_json", "done")
    return res_json


def save_json(json_obj, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as outfile:
        json.dump(json_obj, outfile)


@dataclass(init=False)
class Render:
    id: str
    author: str = field(init=False, default=None)
    image: str = field(init=False, default=None)
    image_url: str = field(init=False, default=None)
    image_path: Path = field(init=False, default=None)
    thumbnail: str = field(init=False, default=None)
    thumbnail_url: str = field(init=False, default=None)
    thumbnail_path: Path = field(init=False, default=None)
    thumbnail_icon_id: int = field(init=False, default=None)

    def __init__(self, id, material):
        self.id = id
        self.material = weakref.ref(material)

    @property
    def cache_dir(self):
        return self.material().cache_dir

    def get_info(self, cache_chek=True):
        json_data = request_json(f"{URL}/renders/{self.id}", None,
                                 self.cache_dir / f"R-{self.id[:8]}.json", cache_chek)

        self.author = json_data['author']
        self.image = json_data['image']
        self.image_url = json_data['image_url']
        self.thumbnail = json_data['thumbnail']
        self.thumbnail_url = json_data['thumbnail_url']

    def get_image(self, cache_check=True):
        self.image_path = download_file(self.image_url,
                                        self.cache_dir / self.image, cache_check)

    def get_thumbnail(self, cache_check=True):
        self.thumbnail_path = download_file(self.thumbnail_url,
                                            self.cache_dir / self.thumbnail, cache_check)

    def thumbnail_load(self, pcoll):
        thumb = pcoll.get(self.thumbnail)
        if not thumb:
            thumb = pcoll.load(self.thumbnail, str(self.thumbnail_path), 'IMAGE')
        self.thumbnail_icon_id = thumb.icon_id


@dataclass(init=False)
class Package:
    id: str
    author: str = field(init=False, default=None)
    label: str = field(init=False, default=None)
    file: str = field(init=False, default=None)
    file_url: str = field(init=False, default=None)
    size_str: str = field(init=False, default=None)

    def __init__(self, id, material):
        self.id = id
        self.material = weakref.ref(material)
        self.size_load = None

    @property
    def cache_dir(self):
        return self.material().cache_dir / f"P-{self.id[:8]}"

    @property
    def file_path(self):
        return self.cache_dir / self.file

    @property
    def has_file(self):
        return self.file_path.is_file()

    def get_info(self, cache_check=True):
        json_data = request_json(f"{URL}/packages/{self.id}", None,
                                 self.cache_dir / "info.json", cache_check)

        self.author = json_data['author']
        self.file = json_data['file']
        self.file_url = json_data['file_url']
        self.label = json_data['label']
        self.size_str = json_data['size']

    def download(self, cache_check=True):
        def callback(size):
            self.size_load = size
            update_ui()

        download_file_callback(self.file_url, self.file_path, callback, cache_check)

    def unzip(self, path=None, cache_check=True):
        if not path:
            path = self.cache_dir / "package"

        if path.is_dir() and not cache_check:
            shutil.rmtree(path, ignore_errors=True)

        if not path.is_dir():
            with zipfile.ZipFile(self.file_path) as z:
                z.extractall(path=path)

        mtlx_file = next(path.glob("**/*.mtlx"))
        return mtlx_file

    @property
    def size(self):
        n, b = self.size_str.split(" ")
        size = float(n)
        if b == "MB":
            size *= 1048576 # 2 ** 20
        elif b == "KB":
            size *= 1024    # 2 ** 10
        elif b == "GB":
            size *= 2 ** 30

        return int(size)

    def __lt__(self, other):
        return self.size < other.size


@dataclass
class Category:
    id: str
    title: str = field(init=False, default=None)

    @property
    def cache_dir(self):
        return MATLIB_DIR

    def get_info(self, use_cache=True):
        if not self.id:
            return

        json_data = request_json(f"{URL}/categories/{self.id}", None,
                                 self.cache_dir / f"C-{self.id[:8]}.json", use_cache)

        self.title = json_data['title']

    def __lt__(self, other):
        return self.title < other.title


@dataclass(init=False)
class Material:
    id: str
    author: str
    title: str
    description: str
    category: Category
    status: str
    renders: list[Render]
    packages: list[Package]

    def __init__(self, mat_json):
        self.id = mat_json['id']
        self.author = mat_json['author']
        self.title = mat_json['title']
        self.description = mat_json['description']
        self.category = Category(mat_json['category'])
        self.status = mat_json['status']

        self.renders = []
        for id in mat_json['renders_order']:
            self.renders.append(Render(id, self))

        self.packages = []
        for id in mat_json['packages']:
            self.packages.append(Package(id, self))

        save_json(mat_json, self.cache_dir / "info.json")

    def __lt__(self, other):
        return self.title.lower() < other.title.lower()

    @property
    def cache_dir(self):
        return MATLIB_DIR / f"M-{self.id[:8]}"

    @classmethod
    def get_materials(cls):
        offset = 0
        limit = 500

        while True:
            res_json = request_json(f"{URL}/materials", {'limit': limit, 'offset': offset}, None)

            count = res_json['count']

            for mat_json in res_json['results']:
                mat = Material(mat_json)
                if not mat.packages or not mat.category.id:
                    continue

                yield mat

            offset += limit
            if offset >= count:
                break

    @classmethod
    def get_materials_cache(cls):
        for f in MATLIB_DIR.glob("M-*/info.json"):
            with open(f) as json_file:
                mat_json = json.load(json_file)

            yield Material(mat_json)


class Manager:
    def __init__(self):
        self.materials = None
        self.categories = None
        self.pcoll = None
        self.load_thread = None
        self.package_executor = None
        self.status = ""
        self.is_synced = None

    def __del__(self):
        # bpy.utils.previews.remove(self.pcoll)
        pass

    def set_status(self, msg):
        self.status = msg
        update_ui()

    @property
    def materials_list(self):
        # required for thread safe purposes
        return list(manager.materials.values())

    @property
    def categories_list(self):
        # required for thread safe purposes
        return list(manager.categories.values())

    def check_load_materials(self, reset=False):
        # required is not None condition to prevent further update if no material is found at first time.
        if self.materials is not None and not reset:
            return True

        if reset:
            bpy.utils.previews.remove(self.pcoll)

        self.materials = {}
        self.categories = {}
        self.pcoll = bpy.utils.previews.new()

        def category_load(cat):
            cat.get_info()
            self.categories[cat.id] = cat

        def material_load(mat, is_cached):
            for render in mat.renders:
                render.get_info()
                render.get_thumbnail()
                render.thumbnail_load(self.pcoll)

            for package in mat.packages:
                package.get_info()

            self.materials[mat.id] = mat

            self.set_status(f"Syncing {len(self.materials)} {'cached' if is_cached else 'online'} materials...")

        def load():
            self.is_synced = False
            self.set_status("Start syncing...")
            with futures.ThreadPoolExecutor() as executor:
                try:
                    #
                    # getting cached materials
                    #
                    materials = {mat.id: mat for mat in Material.get_materials_cache()}
                    categories = {mat.category.id: mat.category for mat in materials.values()}

                    # loading categories
                    category_loaders = [executor.submit(category_load, cat)
                                        for cat in categories.values()]
                    for future in futures.as_completed(category_loaders):
                        future.result()

                    # updating category for cached materials
                    for mat in materials.values():
                        mat.category.get_info()

                    # loading cached materials
                    material_loaders = [executor.submit(material_load, mat, True)
                                        for mat in materials.values()]
                    for future in futures.as_completed(material_loaders):
                        future.result()

                    #
                    # getting and syncing with online materials
                    #
                    online_materials = {mat.id: mat for mat in Material.get_materials()}

                    # loading new categories
                    new_categories = {}
                    for mat in online_materials.values():
                        cat = mat.category
                        if cat.id not in categories and cat.id not in new_categories:
                            new_categories[cat.id] = cat

                    category_loaders = [executor.submit(category_load, cat)
                                        for cat in new_categories.values()]
                    for future in futures.as_completed(category_loaders):
                        future.result()

                    # updating categories for online materials
                    for mat in online_materials.values():
                        mat.category.get_info()

                    # loading online materials
                    material_loaders = [executor.submit(material_load, mat, False)
                                        for mat in online_materials.values()]
                    for future in futures.as_completed(material_loaders):
                        future.result()

                    self.set_status(f"Syncing {len(self.materials)} materials completed")

                except requests.exceptions.RequestException as err:
                    executor.shutdown(wait=True, cancel_futures=True)
                    self.set_status(f"Connection error. Synced {len(self.materials)} materials")
                    log.error(err)

                finally:
                    self.is_synced = True

        self.load_thread = threading.Thread(target=load, daemon=True)
        self.load_thread.start()

        return False

    def load_package(self, package):
        package.size_load = 0

        def package_load():
            try:
                package.download()

            except requests.exceptions.RequestException as err:
                log.error(err)
                package.size_load = None

            update_ui()

        if not self.package_executor:
            self.package_executor = futures.ThreadPoolExecutor()

        self.package_executor.submit(package_load)


manager = Manager()
