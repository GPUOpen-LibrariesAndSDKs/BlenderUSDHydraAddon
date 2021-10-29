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

from . import LIBS_DIR

from ..utils import logging
log = logging.Log(tag='utils.matlib')

URL = "https://matlibapi.stvcis.com/api"
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

    def load():
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

    load_thread = threading.Thread(target=load)
    load_thread.start()
    return load_thread


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
        self.size_load = 0
        self.load_thread = None

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

        self.load_thread = download_file_callback(self.file_url, self.cache_dir / self.file,
                                                  callback, cache_check)

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
            size *= 2 ^ 20
        elif b == "KB":
            size *= 2 ^ 10

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
        return self.title < other.title

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
