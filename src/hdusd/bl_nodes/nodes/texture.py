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
from ... import utils
from . import log


TEXTURE_ERROR_COLOR = (1.0, 0.0, 1.0)  # following Cycles color for wrong Texture nodes

# image format conversion for packed pixel/generated images
IMAGE_FORMATS = {
    'OPEN_EXR_MULTILAYER': ('OPEN_EXR', 'exr'),
    'OPEN_EXR': ('OPEN_EXR', 'exr'),
    'HDR': ('HDR', 'hdr'),
    'TARGA': ('TARGA', 'tga'),
    'TARGA_RAW': ('TARGA', 'tga'),
    # TIFF and everything else will be stored as PNG
}
DEFAULT_FORMAT = ('PNG', 'png')


class ShaderNodeTexImage(NodeParser):
    def export(self):
        image_error_result = self.node_item(TEXTURE_ERROR_COLOR)
        image = self.node.image

        # TODO support UDIM Tilesets and SEQUENCE
        if not image or image.source in ('TILED', 'SEQUENCE'):
            return image_error_result

        # there were scenes in Linux that have 0x0x0 image packed
        if image.size[0] * image.size[1] * image.channels == 0:
            return image_error_result

        file_path = image.filepath_from_user()
        if image.source != 'FILE' or image.is_dirty or not os.path.isfile(file_path):  # generated, edited and packed
            target_format, target_extension = IMAGE_FORMATS.get(image.file_format, DEFAULT_FORMAT)
            temp_path = utils.get_temp_file(f"{hash(image.name)}.texture.{target_extension}")
            if not os.path.isfile(temp_path):
                image.save_render(str(temp_path))
            img_path = str(temp_path)
        else:
            img_path = file_path

        # TODO use Vector input for UV
        uv = self.create_node('texcoord', 'vector2', {})

        result = self.create_node('image', 'color3', {
            'texcoord': uv,
        })
        result.set_parameter('file', img_path)

        return result

class ShaderNodeTexNoise(NodeParser):
    def export(self):
        # wanted to use, did nothing
        #  <nodedef name="ND_noise2d_float" node="noise2d" nodegroup="procedural2d">
        #    <parameter name="amplitude" type="float" value="1.0"/>
        #    <parameter name="pivot" type="float" value="0.0"/>
        #    <input name="texcoord" type="vector2" defaultgeomprop="UV0"/>
        #    <output name="out" type="float" default="0.0"/>
        #  </nodedef>

        # used instead
        #  <nodedef name="ND_noise3d_float" node="noise3d" nodegroup="procedural3d">
        #    <parameter name="amplitude" type="float" value="1.0"/>
        #    <parameter name="pivot" type="float" value="0.0"/>
        #    <input name="position" type="vector3" defaultgeomprop="Pobject"/>
        #    <output name="out" type="float" default="0.0"/>
        #  </nodedef>


        scale = self.get_input_value('Scale')
        # scale *= 0.6  # RPR Noise texture visually is about 60% of Blender Noise

        # apply scale via UV
        uv = self.create_node('texcoord', 'vector2', {})

        # uv /= scale

        #result = self.create_node('noise2d', 'float', {
        #result = self.create_node('noise2d', 'color3', {
        result = self.create_node('noise3d', 'float', {})
#        result.set_parameter('position', uv)

        # amplitude - leave at 1.0
        # pivot - leave at 0.0

        return result

