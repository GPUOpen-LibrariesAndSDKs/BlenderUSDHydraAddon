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
import math

from ..node_parser import NodeParser
from ...utils import logging
log = logging.Log(tag='export.bl_nodes.nodes')


# INPUTS

class ShaderNodeValue(NodeParser):
    """ simply return val """

    def export(self):
        return self.get_output_default()


class ShaderNodeRGB(NodeParser):
    """ simply return val """

    def export(self):
        return self.get_output_default()


# TEXTURES


# SHADERS

class ShaderNodeBsdfPrincipled(NodeParser):
    def export(self):
        def enabled(val):
            if val is None:
                return False

            if isinstance(val.data, float) and math.isclose(val.data, 0.0):
                return False

            if isinstance(val.data, tuple) and \
               math.isclose(val.data[0], 0.0) and \
               math.isclose(val.data[1], 0.0) and \
               math.isclose(val.data[2], 0.0):
                return False

            return True

        # GETTING REQUIRED INPUTS
        # Note: if some inputs are not needed they won't be taken

        base_color = self.get_input_value('Base Color')

        subsurface = self.get_input_value('Subsurface')
        subsurface_radius = None
        subsurface_color = None
        if enabled(subsurface):
            subsurface_radius = self.get_input_value('Subsurface Radius')
            subsurface_color = self.get_input_value('Subsurface Color')

        metallic = self.get_input_value('Metallic')
        specular = self.get_input_value('Specular')
        specular_tint = self.get_input_value('Specular Tint')
        roughness = self.get_input_value('Roughness')

        anisotropic = None
        anisotropic_rotation = None
        if enabled(metallic):
            # TODO: use Specular Tint input
            anisotropic = self.get_input_value('Anisotropic')
            if enabled(anisotropic):
                anisotropic_rotation = self.get_input_value('Anisotropic Rotation')
                # anisotropic_rotation = 0.5 - (anisotropic_rotation % 1.0)

        sheen = self.get_input_value('Sheen')
        sheen_tint = None
        if enabled(sheen):
            sheen_tint = self.get_input_value('Sheen Tint')

        clearcoat = self.get_input_value('Clearcoat')
        clearcoat_roughness = None
        if enabled(clearcoat):
            clearcoat_roughness = self.get_input_value('Clearcoat Roughness')

        ior = self.get_input_value('IOR')

        transmission = self.get_input_value('Transmission')
        transmission_roughness = None
        if enabled(transmission):
            transmission_roughness = self.get_input_value('Transmission Roughness')

        emission = self.get_input_value('Emission')
        emission_strength = self.get_input_value('Emission Strength')

        alpha = self.get_input_value('Alpha')
        # transparency = 1.0 - alpha

        normal = self.get_input_link('Normal')
        clearcoat_normal = self.get_input_link('Clearcoat Normal')
        tangent = self.get_input_link('Tangent')

        # CREATING STANDARD SURFACE
        result = self.create_node('standard_surface', 'surfaceshader', {
            'base': 1.0,
            'base_color': base_color,
            'diffuse_roughness': roughness,
            'normal': normal,
            'tangent': tangent,
        })

        if enabled(metallic):
            result.set_input('metalness', metallic)

        if enabled(specular):
            result.set_inputs({
                'specular': specular,
                'specular_color': base_color,
                'specular_roughness': roughness,
                'specular_IOR': ior,
                'specular_anisotropy': anisotropic,
                'specular_rotation': anisotropic_rotation,
            })

        if enabled(transmission):
            result.set_inputs({
                'transmission': transmission,
                'transmission_color': base_color,
                'transmission_extra_roughness': transmission_roughness,
            })

        if enabled(subsurface):
            result.set_inputs({
                'subsurface': subsurface,
                'subsurface_color': subsurface_color,
                'subsurface_radius': subsurface_radius,
                'subsurface_anisotropy': anisotropic,
            })

        if enabled(sheen):
            result.set_inputs({
                'sheen': sheen,
                'sheen_color': base_color,
                'sheen_roughness': roughness,
            })

        if enabled(clearcoat):
            result.set_inputs({
                'coat': clearcoat,
                'coat_color': base_color,
                'coat_roughness': clearcoat_roughness,
                'coat_IOR': ior,
                'coat_anisotropy': anisotropic,
                'coat_rotation': anisotropic_rotation,
                'coat_normal': clearcoat_normal,
            })

        if enabled(emission):
            result.set_inputs({
                'emission': emission_strength,
                'emission_color': emission,
            })

        return result


class ShaderNodeBsdfDiffuse(NodeParser):
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


class ShaderNodeBsdfGlass(NodeParser):
    def export(self):
        color = self.get_input_value('Color')
        roughness = self.get_input_value('Roughness')
        ior = self.get_input_value('IOR')
        normal = self.get_input_link('Normal')

        # CREATING STANDARD SURFACE
        result = self.create_node('standard_surface', 'surfaceshader', {
            'base': 0.0,
            'normal': normal,
            'specular': 1.0,
            'specular_color': color,
            'specular_roughness': roughness,
            'specular_IOR': ior,
            'specular_anisotropy': 0.0,
            'specular_rotation': 0.0,
            'transmission': 1.0,
            'transmission_color': color,
            'transmission_extra_roughness': roughness,
        })

        return result


class ShaderNodeEmission(NodeParser):
    def export(self):
        color = self.get_input_value('Color')
        strength = self.get_input_value('Strength')

        result = self.create_node('uniform_edf', 'EDF', {
            'color': color * strength,
        })

        return result


# COLOR

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


# CONVERTER

class ShaderNodeMath(NodeParser):
    """ Map Blender operations to MaterialX definitions, see the stdlib_defs.mtlx in MaterialX """

    def export(self):
        op = self.node.operation
        in1 = self.get_input_value(0)
        # single operand operations
        if op == 'SINE':
            res = in1.sin()
        elif op == 'COSINE':
            res = in1.cos()
        elif op == 'TANGENT':
            res = in1.tan()
        elif op == 'ARCSINE':
            res = in1.asin()
        elif op == 'ARCCOSINE':
            res = in1.acos()
        elif op == 'ARCTANGENT':
            res = in1.atan()
        elif op == 'LOGARITHM':
            res = in1.log()
        elif op == 'ABSOLUTE':
            res = abs(in1)
        elif op == 'FLOOR':
            res = in1.floor()
        elif op == 'FRACT':
            res = in1 % 1.0
        elif op == 'CEIL':
            res = in1.ceil()
        elif op == 'ROUND':
            f = in1.floor()
            res = (in1 % 1.0 < 0.5).if_else(f, f + 1.0)

        else:  # 2-operand operations
            in2 = self.get_input_value(1)

            if op == 'ADD':
                res = in1 + in2
            elif op == 'SUBTRACT':
                res = in1 - in2
            elif op == 'MULTIPLY':
                res = in1 * in2
            elif op == 'DIVIDE':
                res = in1 / in2
            elif op == 'POWER':
                res = in1 ** in2
            elif op == 'MINIMUM':
                res = in1.min(in2)
            elif op == 'MAXIMUM':
                res = in1.max(in2)

            else:
                in3 = self.get_input_value(2)

                if op == 'MULTIPLY_ADD':
                    res = in1 * in2 + in3
                else:
                    log.warn("Unsupported math operation", op)
                    return None

        if self.node.use_clamp:
            res = res.clamp()

        return res


class ShaderNodeMixShader(NodeParser):

    def export(self):
        factor = self.get_input_value(0)
        shader1 = self.get_input_link(1)
        shader2 = self.get_input_link(2)

        if shader1 is None and shader2 is None:
            return None

        if shader1 is None:
            return shader2

        if shader2 is None:
            return shader1

        result = self.create_node('mix_bsdf', 'surfaceshader', {
            'fg': shader1,
            'bg': shader2,
            'mix': factor
        })
        return result


class ShaderNodeAddShader(NodeParser):

    def export(self):
        shader1 = self.get_input_link(0)
        shader2 = self.get_input_link(1)

        log.info(f"shader1 {shader1}")
        log.info(f"shader2 {shader2}")

        if shader1 is None and shader2 is None:
            return None

        if shader1 is None:
            return shader2

        if shader2 is None:
            return shader1

        result = self.create_node('add_bsdf', 'surfaceshader', {
            'in1': shader1,
            'in2': shader2
        })
        return result
