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

DEFAULT_SPACE = 'OBJECT'


class ShaderNodeNormalMap(NodeParser):
    def export(self):
        color = self.get_input_value('Color')
        strength = self.get_input_value('Strength')
        space = self.node.space

        if space not in ('TANGENT', 'OBJECT'):
            log.warn("Ignoring unsupported Space", space, self.node, self.material,
                     f"{DEFAULT_SPACE} will be used")
            space = DEFAULT_SPACE

        if space == 'TANGENT':
            log.warn("Ignoring unsupported UV Map", space, self.node, self.material,
                     "No UV Map will be used")

        result = self.create_node('normalmap', 'vector3', {
            'in': color ,
            'scale': strength,
            'space': space.lower(),
        })

        return result
