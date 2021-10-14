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


class HdUSD_Operator(bpy.types.Operator):
    COMPAT_ENGINES = {'HdUSD'}

    @classmethod
    def poll(cls, context):
        return context.engine in cls.COMPAT_ENGINES


class HdUSD_Panel(bpy.types.Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'render'
    COMPAT_ENGINES = {'HdUSD'}

    @classmethod
    def poll(cls, context):
        return context.engine in cls.COMPAT_ENGINES


class HdUSD_ChildPanel(bpy.types.Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_parent_id = ''


from . import (
    panels,
    render,
    hdrpr_render,
    light,
    material,
    matlib,
    world,
    usd_list,
    mx_nodes,
    object,
)


register_classes, unregister_classes = bpy.utils.register_classes_factory([
    render.HDUSD_OP_open_web_page,
    render.HDUSD_OP_data_source,
    render.HDUSD_OP_nodetree_camera,
    render.HDUSD_MT_data_source_final,
    render.HDUSD_MT_nodetree_camera_final,
    render.HDUSD_MT_data_source_viewport,
    render.HDUSD_RENDER_PT_render_settings_final,
    render.HDUSD_RENDER_PT_render_settings_viewport,
    render.HDUSD_RENDER_PT_help_about,
    render.HDUSD_RENDER_PT_debug,

    hdrpr_render.HDUSD_RENDER_PT_hdrpr_settings_final,
    hdrpr_render.HDUSD_RENDER_PT_hdrpr_settings_samples_final,
    hdrpr_render.HDUSD_RENDER_PT_hdrpr_settings_quality_final,
    hdrpr_render.HDUSD_RENDER_PT_hdrpr_settings_denoise_final,
    hdrpr_render.HDUSD_RENDER_PT_hdrpr_settings_viewport,
    hdrpr_render.HDUSD_RENDER_PT_hdrpr_settings_samples_viewport,
    hdrpr_render.HDUSD_RENDER_PT_hdrpr_settings_quality_viewport,
    hdrpr_render.HDUSD_RENDER_PT_hdrpr_settings_denoise_viewport,

    light.HDUSD_LIGHT_PT_light,

    material.HDUSD_MATERIAL_PT_context,
    material.HDUSD_MATERIAL_PT_preview,
    material.HDUSD_MATERIAL_OP_new_mx_node_tree,
    material.HDUSD_MATERIAL_OP_duplicate_mx_node_tree,
    material.HDUSD_MATERIAL_OP_duplicate_mat_mx_node_tree,
    material.HDUSD_MATERIAL_OP_link_mx_node_tree,
    material.HDUSD_MATERIAL_OP_unlink_mx_node_tree,
    material.HDUSD_MATERIAL_MT_mx_node_tree,
    material.HDUSD_MATERIAL_PT_material,
    material.HDUSD_MATERIAL_PT_output_surface,
    material.HDUSD_MATERIAL_PT_output_displacement,
    material.HDUSD_MATERIAL_PT_output_volume,
    material.HDUSD_MATERIAL_OP_export_mx_file,
    material.HDUSD_MATERIAL_OP_export_mx_console,
    material.HDUSD_MATERIAL_PT_export_mx,

    matlib.HDUSD_MATERIAL_OP_matlib_clear_search,
    matlib.HDUSD_MATLIB_OP_import_material,
    matlib.HDUSD_MATLIB_OP_load_package,
    matlib.HDUSD_MATLIB_OP_select_package,
    matlib.HDUSD_MATLIB_PT_matlib,
    matlib.HDUSD_MATLIB_MT_package_menu,

    world.HDUSD_WORLD_PT_surface,

    usd_list.HDUSD_OP_usd_list_item_expand,
    usd_list.HDUSD_OP_usd_list_item_show_hide,
    usd_list.HDUSD_OP_usd_tree_node_print_stage,
    usd_list.HDUSD_OP_usd_tree_node_print_root_layer,
    usd_list.HDUSD_UL_usd_list_item,
    usd_list.HDUSD_NODE_PT_usd_list,
    usd_list.HDUSD_OP_usd_nodetree_add_basic_nodes,
    usd_list.HDUSD_NODE_PT_usd_nodetree_tree_tools,
    usd_list.HDUSD_NODE_PT_usd_nodetree_node_tools,

    mx_nodes.HDUSD_MX_OP_import_file,
    mx_nodes.HDUSD_MX_OP_export_file,
    mx_nodes.HDUSD_MX_OP_export_console,
    mx_nodes.HDUSD_MX_OP_create_basic_nodes,
    mx_nodes.HDUSD_MX_MATERIAL_PT_import_export,

    object.HDUSD_OBJECT_PT_usd_settings,
    object.HDUSD_OP_usd_object_show_hide,
])


def register():
    panels.register()
    register_classes()


def unregister():
    panels.unregister()
    unregister_classes()
