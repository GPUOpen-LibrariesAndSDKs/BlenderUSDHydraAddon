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
from .node_parser import NodeParser


class ShaderNodeOutputWorld(NodeParser):
    def export(self):
        color = self.get_input_value('Color')
        roughness = self.get_input_value('Roughness')
        normal = self.get_input_link('Normal')

        result = self.create_node('diffuse_brdf', 'BSDF', {
            'color': color,
            'roughness': roughness,
            'normal': normal,
        })

        return result
