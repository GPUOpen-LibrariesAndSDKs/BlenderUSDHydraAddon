# **********************************************************************
# Copyright 2023 Advanced Micro Devices, Inc
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
# ********************************************************************
from .node_parser import NodeParser


class ShaderNodeOutputWorld(NodeParser):
    def __init__(self, world, node, **kwargs):
        super().__init__(world, node, None, **kwargs)

    def export(self):
        return self.get_input_link('Surface')


class ShaderNodeBackground(NodeParser):
    def export(self):
        color = self.get_input_value('Color').data
        strength = self.get_input_scalar('Strength').data

        return self.node_item({
            'color': color,
            'intensity': strength
        })


class ShaderNodeTexEnvironment(NodeParser):
    def export(self):
        return self.node_item({
            'image': self.node.image
        })


class ShaderNodeTexImage(NodeParser):
    def export(self):
        return self.node_item({
            'image': self.node.image
        })


class ShaderNodeRGB(NodeParser):
    def export(self):
        return self.get_output_default()


class ShaderNodeValue(NodeParser):
    def export(self):
        return self.get_output_default()


class ShaderNodeInvert(NodeParser):
    def export(self):
        fac = self.get_input_scalar('Fac')
        color = self.get_input_scalar('Color')

        return fac.blend(color, 1.0 - color)
