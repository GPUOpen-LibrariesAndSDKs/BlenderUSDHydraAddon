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


SSS_MIN_RADIUS = 0.0001


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

    def export_rpr(self):
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
        transparency = 1.0 - alpha

        normal = self.get_input_link('Normal')
        clearcoat_normal = self.get_input_link('Clearcoat Normal')
        tangent = self.get_input_link('Tangent')

        # CREATING STANDARD SURFACE
        result = self.create_node('rpr_uberv2', 'surfaceshader')

        # looks like diffuse should be always enabled, regarding cycles
        result.set_inputs({
            'uber_diffuse_color': base_color,
            'uber_diffuse_weight': 1.0,
            'uber_diffuse_roughness': roughness,
            'uber_diffuse_normal': normal,
            'uber_backscatter_weight': 0.0,
        })

        # setting reflection weight as max of specular and metallic weights
        result.set_inputs({
            'uber_reflection_weight': specular.max(metallic),
            'uber_reflection_roughness': roughness,
            'uber_reflection_mode': 'Metalness',
            'uber_reflection_metalness': metallic,
            'uber_reflection_color': base_color,
            'uber_diffuse_normal': normal,
        })

        if enabled(anisotropic):
            result.set_inputs({
                'uber_reflection_anisotropy': anisotropic,
                'uber_reflection_anisotropy_rotation': anisotropic_rotation,
            })

        # Clearcloat
        if enabled(clearcoat):
            result.set_inputs({
                'uber_coating_color': (1.0, 1.0, 1.0),
                'uber_coating_weight': clearcoat,
                'uber_coating_roughness': clearcoat_roughness,
                'uber_coating_thickness': 0.0,
                'uber_coating_transmission_color': (0.0, 0.0, 0.0),
                'uber_coating_mode': 'PBR',
                'uber_coating_ior': ior,
            })
            if enabled(clearcoat_normal):
                result.set_input('uber_coating_normal', clearcoat_normal)
            elif enabled(normal):
                result.set_input('uber_coating_normal', normal)

        # Sheen
        if enabled(sheen):
            result.set_inputs({
                'uber_sheen_weight': sheen,
                'uber_sheen': base_color,
                'uber_sheen_tint': sheen_tint,
            })

        # Subsurface
        if enabled(subsurface):
            # check for 0 channel value(for Cycles it means "light shall not pass"
            # unlike "pass it all" of RPR) that's why we check it with small value like 0.0001
            subsurface_radius = subsurface_radius.max(SSS_MIN_RADIUS)

            result.set_inputs({
                'uber_sss_weight': subsurface,
                'uber_sss_scatter_color': subsurface_color,
                'uber_sss_scatter_distance': subsurface_radius,
                'uber_sss_multiscatter': False,
                'uber_backscatter_weight': subsurface,
                'uber_backscatter_color': subsurface_color,
            })

        # Emission -> Emission
        if enabled(emission):
            # more related formula for emission weight:
            emission_weight = emission.average_xyz().min(1.0) * 0.5 + 0.5

            result.set_inputs({
                'uber_emission_weight': emission_weight,
                'uber_emission_color': emission,
                'uber_emission_mode': 'Doublesided',
            })

        # Alpha -> Transparency
        if enabled(transparency):
            result.set_input('uber_transparency', transparency)

        # Transmission -> Refraction
        if enabled(transmission):
            result.set_inputs({
                'uber_refraction_weight': transmission,
                'uber_refraction_color': base_color,
                'uber_refraction_roughness': transmission_roughness,
                'uber_refraction_ior': ior,
                'uber_refraction_thin_surface': False,
                'uber_refraction_caustics': True,
                'uber_refraction_normal': normal,
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
