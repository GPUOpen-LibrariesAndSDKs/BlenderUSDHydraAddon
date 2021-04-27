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
import os

from ..node_parser import NodeParser
from . import log


TEXTURE_ERROR_COLOR = (1.0, 0.0, 1.0)  # following Cycles color for wrong Texture nodes


class ShaderNodeTexImage(NodeParser):
    def export(self):
        image = self.node.image
        if not image:
        image_error_result = self.node_item(TEXTURE_ERROR_COLOR)
            log.warn(f"No image provided")
            return image_error_result
        # TODO support SEQUENCE image type
        if image.source != 'FILE':
            log.warn(f"Image {image} is not a file")
            return image_error_result

        file_path = image.filepath_from_user()
        # TODO export images from pixels, including is_dirty images
        if not os.path.isfile(file_path):
            log.warn(f"Image {image} file doesn't exist at {file_path}")
            return image_error_result
        if image.size[0] * image.size[1] * image.channels == 0:
            log.warn(f"Image {image} has no data")
            return image_error_result

        # TODO use Vector input for UV
        uv = self.create_node('texcoord', 'vector2', {})

        result = self.create_node('image', 'color4', {
            'texcoord': uv,
        })
        result.set_parameter('file', file_path)

        return result
