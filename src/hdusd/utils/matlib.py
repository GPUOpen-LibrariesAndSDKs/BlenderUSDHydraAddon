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
from dataclasses import dataclass, field
import shutil
from pathlib import Path
import zipfile
import json

from .. import config
from . import LIBS_DIR

from ..utils import logging
log = logging.Log(tag='utils.matlib', level="debug")

URL = "https://matlibapi.stvcis.online/api"
MATLIB_DIR = LIBS_DIR.parent / "matlib"


def download_file(url, path, use_cache):
    log.debug("Downloading file", f"url: {url}, path: {path}, use_cache: {use_cache}")
    if use_cache and path.is_file():
        log.debug("Downloading file", "cached data found")
        return path

    if not path.parent.is_dir():
        path.parent.mkdir(parents=True)

    log.debug("Downloading file", "no cached data found, requesting from server")
    with requests.get(url, stream=True) as response:
        with open(path, 'wb') as f:
            shutil.copyfileobj(response.raw, f)
    log.debug("Downloading file", "done")

    return path


def request_json(url, path, use_cache):
    log.debug("Requesting json", f"url: {url}, path: {path}, use_cache: {use_cache}")
    if use_cache and path.is_file():
        log.debug("Requesting json", "cached data found")
        with open(path) as json_file:
            return json.load(json_file)

    log.debug("Requesting json", "no cached data found, requesting from server")
    response = requests.get(url)
    res_json = response.json()
    log.debug("Requesting json", "done")

    if not path.parent.is_dir():
        path.parent.mkdir(parents=True)

    with open(path, 'w') as outfile:
        json.dump(res_json, outfile)

    log.debug("Requesting json", f"data cached, path: {path}")
    return res_json


def get_cached_path(path):
    if path.is_file():
        return path

    return None


@dataclass
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

    def get_info(self, use_cache=True):
        json_data = request_json(f"{URL}/renders/{self.id}", (MATLIB_DIR / self.id).with_suffix(".json"),
                             use_cache)

        self.author = json_data['author']
        self.image = json_data['image']
        self.image_url = json_data['image_url']
        self.thumbnail = json_data['thumbnail']
        self.thumbnail_url = json_data['thumbnail_url']

    def get_image(self, use_cache=True):
        self.image_path = download_file(self.image_url, MATLIB_DIR / self.image,
                                        use_cache)

    def get_thumbnail(self, use_cache=True):
        self.thumbnail_path = download_file(self.thumbnail_url, MATLIB_DIR / self.thumbnail,
                                            use_cache)

    def thumbnail_load(self, pcoll):
        thumb = pcoll.load(self.thumbnail, str(self.thumbnail_path), 'IMAGE')
        self.thumbnail_icon_id = thumb.icon_id


@dataclass
class Package:
    id: str
    author: str = field(init=False, default=None)
    label: str = field(init=False, default=None)
    file: str = field(init=False, default=None)
    file_url: str = field(init=False, default=None)
    size: str = field(init=False, default=None)
    file_path: Path = field(init=False, default=None)

    def get_info(self, use_cache=True):
        json_data = request_json(f"{URL}/packages/{self.id}", MATLIB_DIR / self.id / "Package.json",
                             use_cache)

        self.author = json_data['author']
        self.file = json_data['file']
        self.file_url = json_data['file_url']
        self.label = json_data['label']
        self.size = json_data['size']
        self.file_path = get_cached_path(MATLIB_DIR / self.id / self.file)

    def get_file(self, use_cache=True):
        self.file_path = download_file(self.file_url, MATLIB_DIR / self.id / self.file,
                                       use_cache)

    def unzip(self, path=None, use_cache=True):
        if not path:
            path = self.file_path.parent

        if not (use_cache and (path / self.file_path.stem).is_dir()):
            with zipfile.ZipFile(self.file_path) as z:
                z.extractall(path=path)

        mtlx_file = next(path.glob("*/*.mtlx"))
        return mtlx_file


@dataclass
class Category:
    id: str
    title: str = field(init=False, default=None)

    def get_info(self, use_cache=True):
        json_data = request_json(f"{URL}/categories/{self.id}", MATLIB_DIR / self.id / "Category.json",
                             use_cache)

        self.title = json_data['title']


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
        self.category = Category(mat_json['category']) if mat_json['category'] else None
        self.status = mat_json['status']

        self.renders = []
        for id in mat_json['renders_order']:
            self.renders.append(Render(id))

        self.packages = []
        for id in mat_json['packages']:
            self.packages.append(Package(id))

    def get_description(self):
        description = f"{self.title}"
        if self.description:
            description += f"\n{self.description}"
        if self.category:
            description += f"\nCategory: {self.category.title}"
        description += f"\nAuthor: {self.author}"

        return description

    @classmethod
    def get_materials(cls, limit=10, offset=0):
        log.debug("Requesting material",
            f"url: {URL}/materials, params: 'limit': {limit}, 'offset': {offset}")
        response = requests.get(f"{URL}/materials", params={'limit': limit, 'offset': offset})
        res_json = response.json()
        log.debug("Request done")

        for mat_json in res_json['results']:
            mat = Material(mat_json)
            if not mat.packages:
                continue
            yield mat

    @classmethod
    def get_all_materials(cls):
        offset = 0
        limit = 500

        log.debug("Requesting material",
            f"url: {URL}/materials, params: 'limit': {limit}, 'offset': {offset}")
        response = requests.get(f"{URL}/materials", params={'limit': limit, 'offset': offset})
        res_json = response.json()
        log.debug("Request done")

        results = res_json['results']

        while res_json['next'] is not None:
            log.debug("Requesting material", f"{res_json['next']}")
            response = requests.get(res_json['next'])
            res_json = response.json()
            log.debug("Request done")
            results.extend(res_json['results'])

        for mat_json in results:
            mat = Material(mat_json)
            if not mat.packages:
                continue

            yield mat
