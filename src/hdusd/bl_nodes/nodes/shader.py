# **********************************************************************
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


SSS_MIN_RADIUS = 0.0001


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


class ShaderNodeBsdfPrincipled(NodeParser):
    nodegraph_path = ""

    def export(self):
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
    nodegraph_path = ""

    def export(self):
        color = self.get_input_value('Color')
        roughness = self.get_input_value('Roughness')
        normal = self.get_input_link('Normal')

        # Also tried burley_diffuse_bsdf and oren_nayar_diffuse_bsdf here, but Blender crashes with them
        # CREATING STANDARD SURFACE
        result = self.create_node('standard_surface', 'surfaceshader', {
            'base_color': color,
            'diffuse_roughness': 1.0 - roughness,
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
    nodegraph_path = ""

    def export(self):
        result = self.create_node('standard_surface', 'surfaceshader')

        color = self.get_input_value('Color')
        strength = self.get_input_value('Strength')

        if enabled(color) and enabled(strength):
            result.set_inputs({
                'emission': 1.0,
                'emission_color': color * strength,
            })

        return result


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

        result = self.create_node('mix', 'BSDF', {
            'fg': shader1,
            'bg': shader2,
            'mix': factor
        })
        return result


class ShaderNodeAddShader(NodeParser):
    def export(self):
        shader1 = self.get_input_link(0)
        shader2 = self.get_input_link(1)

        if shader1 is None and shader2 is None:
            return None

        if shader1 is None:
            return shader2

        if shader2 is None:
            return shader1

        result = self.create_node('add', 'BSDF', {
            'in1': shader1,
            'in2': shader2
        })
        return result
