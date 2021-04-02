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
from . import log


class ShaderNodeInvert(NodeParser):
    def export(self):
        fac = self.get_input_value('Fac')
        color = self.get_input_value('Color')

        return fac.blend(color, 1.0 - color)


class ShaderNodeMixRGB(NodeParser):

    def export(self):
        fac = self.get_input_value('Fac')
        color1 = self.get_input_value('Color1')
        color2 = self.get_input_value('Color2')

        # these mix types are copied from cycles OSL
        blend_type = self.node.blend_type

        if blend_type in ('MIX', 'COLOR'):
            res = fac.blend(color1, color2)

        elif blend_type == 'ADD':
            res = fac.blend(color1, color1 + color2)

        elif blend_type == 'MULTIPLY':
            res = fac.blend(color1, color1 * color2)

        elif blend_type == 'SUBTRACT':
            res = fac.blend(color1, color1 - color2)

        elif blend_type == 'DIVIDE':
            res = fac.blend(color1, color1 / color2)

        elif blend_type == 'DIFFERENCE':
            res = fac.blend(color1, abs(color1 - color2))

        elif blend_type == 'DARKEN':
            res = fac.blend(color1, color1.min(color2))

        elif blend_type == 'LIGHTEN':
            res = fac.blend(color1, color1.max(color2))

        elif blend_type == 'VALUE':
            res = color1

        elif blend_type == 'SCREEN':
            tm = 1.0 - fac
            res = 1.0 - (tm + fac * (1.0 - color2)) * (1.0 - color1)

        elif blend_type == 'SOFT_LIGHT':
            tm = 1.0 - fac
            scr = 1.0 - (1.0 - color2) * (1.0 - color1)
            res = tm * color1 + fac * ((1.0 - color1) * color2 * color1 + color1 * scr)

        elif blend_type == 'LINEAR_LIGHT':
            test_val = color2 > 0.5
            res = test_val.if_else(color1 + fac * (2.0 * (color2 - 0.5)),
                                   color1 + fac * (2.0 * color2 - 1.0))

        else:
            # TODO: support operations SATURATION, HUE, SCREEN, BURN, OVERLAY
            log.warn("Ignoring unsupported Blend Type", blend_type, self.node, self.material,
                     "mix will be used")
            res = fac.blend(color1, color2)

        if self.node.use_clamp:
            res = res.clamp()

        return res
