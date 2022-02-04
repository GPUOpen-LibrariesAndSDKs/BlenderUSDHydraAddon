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
BLENDER_DEFAULT_COLOR_MODE = "RGB"
READONLY_IMAGE_FORMATS = {".dds"}  # blender can read these formats, but can't write


def cache_image_file(image: bpy.types.Image, cache_check=True):
    image_path = Path(image.filepath_from_user())
    if not image.packed_file and image.source != 'GENERATED':
        if not image_path.is_file():
            log.warn("Image is missing", image, image_path)
            return None

        image_suffix = image_path.suffix.lower()

        if image_suffix in SUPPORTED_FORMATS and\
                f".{image.file_format.lower()}" in SUPPORTED_FORMATS and not image.is_dirty:
            return image_path

        if image_suffix in READONLY_IMAGE_FORMATS:
            return image_path

    temp_path = get_temp_file(DEFAULT_FORMAT, image_path.stem)
    if cache_check and image.source != 'GENERATED' and temp_path.is_file():
        return temp_path

    scene = bpy.context.scene
    user_format = scene.render.image_settings.file_format
    user_color_mode = scene.render.image_settings.color_mode
    scene.render.image_settings.file_format = BLENDER_DEFAULT_FORMAT
    scene.render.image_settings.color_mode = BLENDER_DEFAULT_COLOR_MODE

    try:
        image.save_render(filepath=str(temp_path))
    finally:
        scene.render.image_settings.file_format = user_format
        scene.render.image_settings.color_mode = user_color_mode

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
