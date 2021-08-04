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


def cache_image_file(image: bpy.types.Image):
    if image.source == 'FILE':
        return Path(image.filepath_from_user())

    temp_path = get_temp_file(".png")
    image.save_render(str(temp_path))
    return temp_path
