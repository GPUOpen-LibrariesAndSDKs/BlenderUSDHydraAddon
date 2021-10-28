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
from pathlib import Path

import bpy

from . import get_temp_file
from . import log


SUPPORTED_FORMATS = {".png", ".jpeg", ".jpg", ".hdr", ".tga", ".bmp"}
DEFAULT_FORMAT = ".hdr"
BLENDER_DEFAULT_FORMAT = "HDR"


def cache_image_file(image: bpy.types.Image, cache_check=True):
    # at fist start image.has_data = False even if filepath correct
    if not image.has_data:
        temp_path = Path(image.filepath_from_user())
        if not temp_path.is_file():
            log.warn("Image is missing", image, image.filepath)
            return None

    if not image.packed_file and image.source != 'GENERATED' and \
            Path(image.filepath).suffix.lower() in SUPPORTED_FORMATS and \
            f".{image.file_format.lower()}" in SUPPORTED_FORMATS:
        return Path(image.filepath_from_user())

    # if image packed in .blend file
    old_filepath = image.filepath_raw
    old_file_format = image.file_format

    temp_path = get_temp_file(DEFAULT_FORMAT, image.name)
    if cache_check and image.source != 'GENERATED' and temp_path.is_file():
        return temp_path

    image.filepath_raw = str(temp_path)
    image.file_format = BLENDER_DEFAULT_FORMAT

    try:
        image.save()
    finally:
        image.filepath_raw = old_filepath
        image.file_format = old_file_format

    return temp_path


def cache_image_file_path(image_path, cache_check=True):
    if image_path.suffix.lower() in SUPPORTED_FORMATS:
        return image_path

    if cache_check:
        temp_path = get_temp_file(DEFAULT_FORMAT, image_path.name)
        if temp_path.is_file():
            return temp_path

    image = bpy.data.images.load(str(image_path))
    try:
        return cache_image_file(image, cache_check)

    finally:
        bpy.data.images.remove(image)
