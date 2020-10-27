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
import bpy


PANEL_WIDTH_FOR_COLUMN = 200


class HdUSD_Panel(bpy.types.Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'render'
    COMPAT_ENGINES = {'HdUSD'}

    @classmethod
    def poll(cls, context):
        return context.engine in cls.COMPAT_ENGINES


class HdUSD_Operator(bpy.types.Operator):
    bl_idname = 'hdusd.operator'
    bl_label = "HdUSD Operator"
    COMPAT_ENGINES = {'HdUSD'}

    @classmethod
    def poll(cls, context):
        return context.engine in cls.COMPAT_ENGINES


def get_panels():
    # follow the Cycles model of excluding panels we don't want

    exclude_panels = {
        'DATA_PT_area',
        'DATA_PT_context_light',
        'DATA_PT_falloff_curve',
        'DATA_PT_light',
        'NODE_DATA_PT_light',
        'DATA_PT_shadow',
        'DATA_PT_spot',
        'DATA_PT_sunsky',
        'MATERIAL_PT_context_material',
        'MATERIAL_PT_diffuse',
        'MATERIAL_PT_flare',
        'MATERIAL_PT_halo',
        'MATERIAL_PT_mirror',
        'MATERIAL_PT_options',
        'MATERIAL_PT_pipeline',
        'MATERIAL_PT_preview',
        'MATERIAL_PT_shading',
        'MATERIAL_PT_shadow',
        'MATERIAL_PT_specular',
        'MATERIAL_PT_sss',
        'MATERIAL_PT_strand',
        'MATERIAL_PT_transp',
        'MATERIAL_PT_volume_density',
        'MATERIAL_PT_volume_integration',
        'MATERIAL_PT_volume_lighting',
        'MATERIAL_PT_volume_options',
        'MATERIAL_PT_volume_shading',
        'MATERIAL_PT_volume_transp',
        'RENDERLAYER_PT_layer_options',
        'RENDERLAYER_PT_layer_passes',
        'RENDERLAYER_PT_views',
        'RENDER_PT_antialiasing',
        'RENDER_PT_bake',
        'RENDER_PT_motion_blur',
        'RENDER_PT_performance',
        'RENDER_PT_freestyle',
        'RENDER_PT_post_processing',
        'RENDER_PT_shading',
        'RENDER_PT_simplify',
        'RENDER_PT_stamp',
        'SCENE_PT_simplify',
        'SCENE_PT_audio',
        'WORLD_PT_ambient_occlusion',
        'WORLD_PT_environment_lighting',
        'WORLD_PT_gather',
        'WORLD_PT_indirect_lighting',
        'WORLD_PT_mist',
        'WORLD_PT_preview',
        'WORLD_PT_world',
    }

    panels = []
    for t in bpy.types.Panel.__subclasses__():
        if hasattr(t, 'COMPAT_ENGINES') and 'BLENDER_RENDER' in t.COMPAT_ENGINES:
            if t.__name__ not in exclude_panels:
                panels.append(t)

    return panels


from . import (
    render,
    light,
    material,
    usd_tree,
)


register_classes, unregister_classes = bpy.utils.register_classes_factory([
    render.HDUSD_RENDER_PT_delegate_final,
    render.HDUSD_RENDER_PT_delegate_viewport,

    light.HDUSD_LIGHT_PT_light,

    material.HDUSD_MATERIAL_PT_context,
    material.HDUSD_MATERIAL_PT_surface,
    material.HDUSD_MATERIAL_PT_displacement,
    material.HDUSD_MATERIAL_PT_volume,

    usd_tree.UsdTreeItem_Expand,
    usd_tree.UsdTree_Debug,
    usd_tree.HDUSD_UL_tree_item,
    usd_tree.HDUSD_RENDER_PT_usd,
])


def register():
    # set HdUSD panels filter
    for panel in get_panels():
        panel.COMPAT_ENGINES.add('HdUSD')

    register_classes()


def unregister():
    # remove HdUSD panels filter
    for panel in get_panels():
        if 'HdUSD' in panel.COMPAT_ENGINES:
            panel.COMPAT_ENGINES.remove('HdUSD')

    unregister_classes()
