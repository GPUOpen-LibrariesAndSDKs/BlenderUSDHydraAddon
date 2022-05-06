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
from ..node_parser import NodeParser
from ...utils.image import cache_image_file


TEXTURE_ERROR_COLOR = (1.0, 0.0, 1.0)  # following Cycles color for wrong Texture nodes


class ShaderNodeTexImage(NodeParser):
    def export(self):
        image_error_result = self.node_item(TEXTURE_ERROR_COLOR)
        image = self.node.image

        # TODO support UDIM Tilesets and SEQUENCE
        if not image or image.source in ('TILED', 'SEQUENCE'):
            return image_error_result

        img_path = cache_image_file(image)
        if not img_path:
            return image_error_result

        # TODO use Vector input for UV
        uv = self.create_node('texcoord', 'vector2', {})

        result = self.create_node('image', self.out_type, {
            'file': img_path,
            'texcoord': uv,
        })

        return result
