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
from dataclasses import dataclass
import shutil
from pathlib import Path
import zipfile

from .. import config
from . import temp_pid_dir


URL = config.matlib_url


def download_file(url, path):
    with requests.get(url, stream=True) as response:
        with open(path, 'wb') as f:
            shutil.copyfileobj(response.raw, f)

    return path


@dataclass(init=False)
class Render:
    id: str
    author: str = None
    image: str = None
    image_url: str = None
    image_path: Path = None
    thumbnail: str = None
    thumbnail_url: str = None
    thumbnail_path: Path = None

    def __init__(self, id):
        self.id = id

    def get_info(self):
        response = requests.get(f"{URL}/renders/{self.id}")
        res_json = response.json()
        self.author = res_json['author']
        self.image = res_json['image']
        self.image_url = res_json['image_url']
        self.thumbnail = res_json['thumbnail']
        self.thumbnail_url = res_json['thumbnail_url']

    def get_image(self):
        self.image_path = download_file(self.image_url, temp_pid_dir() / self.image)

    def get_thumbnail(self):
        self.thumbnail_path = download_file(self.thumbnail_url, temp_pid_dir() / self.thumbnail)


@dataclass(init=False)
class Package:
    id: str
    author: str = None
    label: str = None
    file: str = None
    file_url: str = None
    size: str = None
    file_path: Path = None

    def __init__(self, id):
        self.id = id

    def get_info(self):
        response = requests.get(f"{URL}/packages/{self.id}")
        res_json = response.json()
        self.author = res_json['author']
        self.file = res_json['file']
        self.file_url = res_json['file_url']
        self.label = res_json['label']
        self.size = res_json['size']

    def get_file(self):
        self.file_path = download_file(self.file_url, temp_pid_dir() / self.file)

    def unzip(self, path):
        with zipfile.ZipFile(self.file_path) as z:
            z.extractall(path=path)


@dataclass(init=False)
class Material:
    id: str
    author: str
    title: str
    description: str
    renders: list[Render]
    packages: list[Package]

    def __init__(self, mat_json):
        self.id = mat_json['id']
        self.author = mat_json['author']
        self.title = mat_json['title']
        self.description = mat_json['description']

        self.renders = []
        for id in mat_json['renders']:
            self.renders.append(Render(id))

        self.packages = []
        for id in mat_json['packages']:
            self.packages.append(Package(id))

    def get_info(self):
        response = requests.get(f"{URL}/materials/{self.id}")
        res_json = response.json()
        print(res_json)

    @classmethod
    def get_materials(cls, limit=10, offset=0):
        response = requests.get(f"{URL}/materials", params={'limit': limit, 'offset': offset})
        res_json = response.json()
        for mat_json in res_json['results']:
            mat = Material(mat_json)
            yield mat

    @classmethod
    def get_all_materials(cls):
        offset = 0
        limit = 10

        while True:
            mat = None
            for mat in cls.get_materials(limit, offset):
                yield mat

            if not mat:
                break

            offset += limit

