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
import shutil
import MaterialX as mx
import traceback

from pxr import UsdGeom, Usd, Sdf
from bpy_extras.io_utils import ExportHelper
from pathlib import Path

from . import HdUSD_Panel, HdUSD_ChildPanel, HdUSD_Operator
from ..usd_nodes.nodes.base_node import USDNode
from .. import config

from ..utils import logging, get_temp_file, temp_pid_dir
from ..utils.mx import export_mx_to_file, MX_LIBS_DIR
from ..mx_nodes.node_tree import MxNodeTree

log = logging.Log('ui.usd_list')


class HDUSD_OP_usd_list_item_expand(bpy.types.Operator):
    """Expand USD item"""
    bl_idname = "hdusd.usd_list_item_expand"
    bl_label = "Expand"

    index: bpy.props.IntProperty(default=-1)

    def execute(self, context):
        if self.index == -1:
            return {'CANCELLED'}

        node = context.active_node
        usd_list = node.hdusd.usd_list
        items = usd_list.items
        item = items[self.index]

        if len(items) > self.index + 1 and items[self.index + 1].indent > item.indent:
            next_index = self.index + 1
            item_indent = item.indent
            removed_items = 0
            while True:
                if next_index >= len(items):
                    break
                if items[next_index].indent <= item_indent:
                    break
                items.remove(next_index)
                removed_items += 1

            if usd_list.item_index > self.index:
                usd_list.item_index = max(self.index, usd_list.item_index - removed_items)

        else:
            prim = usd_list.get_prim(item)

            added_items = 0
            for child_index, child_prim in enumerate(prim.GetChildren(), self.index + 1):
                child_item = items.add()
                child_item.sdf_path = str(child_prim.GetPath())
                items.move(len(items) - 1, child_index)
                added_items += 1

            if usd_list.item_index > self.index:
                usd_list.item_index += added_items

        return {'FINISHED'}


class HDUSD_OP_usd_list_item_show_hide(bpy.types.Operator):
    """Show/Hide USD item"""
    bl_idname = "hdusd.usd_list_item_show_hide"
    bl_label = "Show/Hide"

    index: bpy.props.IntProperty(default=-1)

    def execute(self, context):
        if self.index == -1:
            return {'CANCELLED'}

        node = context.active_node
        usd_list = node.hdusd.usd_list
        items = usd_list.items
        item = items[self.index]

        prim = usd_list.get_prim(item)
        im = UsdGeom.Imageable(prim)
        if im.ComputeVisibility() == 'invisible':
            im.MakeVisible()
        else:
            im.MakeInvisible()

        return {'FINISHED'}


class HDUSD_UL_usd_list_item(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type not in {'DEFAULT', 'COMPACT'}:
            return

        for i in range(item.indent):
            layout.split(factor=0.1)

        items = data.items
        prim = data.get_prim(item)
        if not prim:
            return

        visible = UsdGeom.Imageable(prim).ComputeVisibility() != 'invisible'

        col = layout.column()
        if not prim.GetChildren():
            icon = 'DOT'
            col.enabled = False
        elif len(items) > index + 1 and items[index + 1].indent > item.indent:
            icon = 'TRIA_DOWN'
        else:
            icon = 'TRIA_RIGHT'

        expand_op = col.operator(HDUSD_OP_usd_list_item_expand.bl_idname, text="", icon=icon,
                                 emboss=False, depress=False)
        expand_op.index = index

        col = layout.column()
        col.label(text=prim.GetName())
        col.enabled = visible

        col = layout.column()
        col.alignment = 'RIGHT'
        col.label(text=prim.GetTypeName())
        col.enabled = visible

        col = layout.column()
        col.alignment = 'RIGHT'
        if prim.GetTypeName() == 'Xform':
            icon = 'HIDE_OFF' if visible else 'HIDE_ON'
        else:
            col.enabled = False
            icon = 'NONE'

        visible_op = col.operator(HDUSD_OP_usd_list_item_show_hide.bl_idname, text="", icon=icon,
                                  emboss=False, depress=False)
        visible_op.index = index


class HDUSD_NODE_PT_usd_list(HdUSD_Panel):
    bl_label = "USD Node Prims"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Item"

    @classmethod
    def poll(cls, context):
        node = context.active_node
        return node and isinstance(node, USDNode)

    def draw(self, context):
        node = context.active_node
        usd_list = node.hdusd.usd_list
        layout = self.layout

        layout.template_list(
            "HDUSD_UL_usd_list_item", "",
            usd_list, "items",
            usd_list, "item_index",
            sort_lock=True
        )

        prop_layout = layout.column()
        prop_layout.use_property_split = True
        for prop in usd_list.prim_properties:
            if prop.type == 'STR' and prop.value_str:
                row = prop_layout.row()
                row.enabled = False
                row.prop(prop, 'value_str', text=prop.name)
            elif prop.type == 'FLOAT':
                prop_layout.prop(prop, 'value_float', text=prop.name)


class HDUSD_OP_usd_nodetree_add_basic_nodes(bpy.types.Operator):
    """Add / Replace to basic USD nodes"""
    bl_idname = "hdusd.usd_nodetree_add_basic_nodes"
    bl_label = "Add Basic Nodes"

    scene_source: bpy.props.EnumProperty(
        items=(('SCENE', 'Scene', 'Render current scene'),
               ('USD_FILE', 'USD File', 'Load and render scene from USD file')),
        default='SCENE',
    )

    def execute(self, context):
        tree = context.space_data.edit_tree
        tree.add_basic_nodes(self.scene_source)
        return {'FINISHED'}


class HDUSD_OP_usd_tree_node_print_stage(HdUSD_Operator):
    """ Print selected USD nodetree node stage to console """
    bl_idname = "hdusd.usd_tree_node_print_stage"
    bl_label = "Print Stage To Console"

    @classmethod
    def poll(cls, context):
        return super().poll(context) and context.space_data.tree_type == 'hdusd.USDTree' and \
               context.active_node

    def execute(self, context):
        tree = context.space_data.edit_tree
        node = context.active_node
        if not node:
            log(f"Unable to print USD nodetree \"{tree.name}\" stage: no USD node selected")
            return {'CANCELLED'}

        # get the USD stage from selected node
        stage = node.cached_stage()
        if not stage:
            log(f"Unable to print USD node \"{tree.name}\":\"{node.name}\" stage: could not get the correct stage")
            return {'CANCELLED'}

        print(f"Node \"{tree.name}\":\"{node.name}\" USD stage is:")
        print(stage.ExportToString())

        return {'FINISHED'}


class HDUSD_OP_usd_tree_node_print_root_layer(HdUSD_Operator):
    """ Print selected USD nodetree node stage to console """
    bl_idname = "hdusd.usd_tree_node_print_root_layer"
    bl_label = "Print Root Layer To Console"

    @classmethod
    def poll(cls, context):
        return super().poll(context) and context.space_data.tree_type == 'hdusd.USDTree' and \
               context.active_node

    def execute(self, context):
        tree = context.space_data.edit_tree
        node = context.active_node
        if not node:
            log(f"Unable to print USD nodetree \"{tree.name}\" stage: no USD node selected")
            return {'CANCELLED'}

        # get the USD stage from selected node
        stage = node.cached_stage()
        if not stage:
            log(f"Unable to print USD node \"{tree.name}\":\"{node.name}\" stage: could not get the correct stage")
            return {'CANCELLED'}

        print(f"Node \"{tree.name}\":\"{node.name}\" USD stage is:")
        print(stage.GetRootLayer().ExportToString())

        return {'FINISHED'}


class HDUSD_NODE_OP_export_usd_file(HdUSD_Operator, ExportHelper):
    bl_idname = "hdusd.export_usd_file"
    bl_label = "USD Export to File"
    bl_description = "Export USD node tree to .usda file"

    filename_ext = ".usda"
    filepath: bpy.props.StringProperty(
        name="File Path",
        description="File path used for exporting material as USD node tree to .usda file",
        maxlen=1024, subtype="FILE_PATH"
    )
    filter_glob: bpy.props.StringProperty(default="*.usda", options={'HIDDEN'}, )

    is_pack_into_one_file: bpy.props.BoolProperty(name="Pack into one file",
                                                  description="Pack all references into one file",
                                                  default=True)

    def execute(self, context):
        tree = context.space_data.edit_tree
        node = context.active_node
        if not node:
            log.warn(f"Unable to export USD nodetree \"{tree.name}\" stage: no USD node selected")
            return {'CANCELLED'}

        # get the USD stage from selected node
        input_stage = node.cached_stage()
        if not input_stage:
            log.warn(f"Unable to export USD node \"{tree.name}\":\"{node.name}\" stage: could not get the correct stage")
            return {'CANCELLED'}

        if not Path(self.filepath).suffix:
            log.warn(f"Unable to export USD node \"{tree.name}\":\"{node.name}\" stage: write correct file name")
            return {'CANCELLED'}

        if self.is_pack_into_one_file:
            input_stage.Export(self.filepath)
            log.warn(f"Export of \"{tree.name}\":\"{node.name}\" stage to {self.filepath}: completed successfuly")
            return {'FINISHED'}

        new_stage = Usd.Stage.CreateNew(str(get_temp_file(".usda")))

        root_layer = new_stage.GetRootLayer()
        root_layer.TransferContent(input_stage.GetRootLayer())

        dest_path_root_dir = Path(self.filepath).parent

        temp_dir = temp_pid_dir()

        def _update_layer_refs(layer, root_path=[]):
            for ref in layer.GetCompositionAssetDependencies():
                ref_name = Path(ref).name
                if Path(ref).suffix == '.mtlx':
                    doc = mx.createDocument()
                    source_path = Path(f"{new_stage.GetPathResolverContext().GetSearchPath()[0]}/{ref}")
                    dest_path = f"{dest_path_root_dir}/{ref_name}"
                    search_path = mx.FileSearchPath(str(source_path.parent))
                    search_path.append(str(MX_LIBS_DIR))
                    mx.readFromXmlFile(doc, str(source_path), searchPath=search_path)

                    mx_node_tree = next((mat.hdusd.mx_node_tree for mat in bpy.data.materials
                                         if mat.hdusd.mx_node_tree
                                         and source_path.stem.startswith(mat.name_full)
                                         and source_path.stem.endswith(mat.hdusd.mx_node_tree.name_full)), None)

                    if not mx_node_tree:
                        mat = bpy.data.materials.get(source_path.stem, None)
                        if not mat:
                            continue

                        mx_node_tree = bpy.data.node_groups.new(f"MX_{mat.name}",
                                                                type=MxNodeTree.bl_idname)

                        mat.hdusd.mx_node_tree = mx_node_tree

                        try:
                            mx_node_tree.import_(doc, source_path)
                        except Exception as e:
                            log.error(traceback.format_exc(), source_path)
                            bpy.data.node_groups.remove(mx_node_tree)
                            continue

                        # after mx_node_tree.import_ deps updated, so we need to change them back since we convert material only to get mx_node_tree
                        layer.UpdateCompositionAssetDependency(f'./{mat.name}{mat.hdusd.mx_node_tree.name}.mtlx', ref)

                        export_mx_to_file(doc, dest_path,
                                          is_export_textures=True,
                                          is_export_deps=True,
                                          mx_node_tree=mx_node_tree,
                                          is_clean_texture_folder=False,
                                          is_clean_deps_folders=False)

                        bpy.data.node_groups.remove(mx_node_tree)

                        continue

                    export_mx_to_file(doc, dest_path,
                                      is_export_textures=True,
                                      is_export_deps=True,
                                      mx_node_tree=mx_node_tree,
                                      is_clean_texture_folder=False,
                                      is_clean_deps_folders=False)
                else:
                    ref_layer_path = str(ref_path if (ref_path := Path(ref)).is_absolute() else Path(layer.realPath).parent.joinpath(ref_path))

                    ref_layer = Sdf.Layer.Find(ref_layer_path)

                    if not temp_dir in Path(ref_layer_path).parents:
                        # if deps is abs, then we need to add its parent dir name, otherwise we add relative path
                        if Path(ref).is_absolute():
                            val = Path(ref_layer_path).parent.name
                        else:
                            val = str(Path(ref).parent)

                        root_path.append(val)

                    if ref_layer.GetCompositionAssetDependencies():
                        _update_layer_refs(ref_layer, root_path)

                    # if deps is not abs, we need to build path from our list to get full path from root to curr layer
                    if temp_dir in Path(ref_layer_path).parents:
                        dest_path = Path(f"{dest_path_root_dir}/{ref_name}")
                    else:
                        dest_path = dest_path_root_dir / "\\".join(root_path) / ref_name

                    ref_layer.Export(str(dest_path))

                    log(f"Export file {ref} to {dest_path}: completed successfuly")

                    # removing path to the current layer before we append new path for the next layer
                    if len(root_path):
                        root_path.pop()

            if layer is root_layer:
                dest_path = f"{dest_path_root_dir}/{Path(self.filepath).name}"
                layer.Export(dest_path)
                log(f"Export file {layer.realPath} to {dest_path}: completed successfuly")

        _update_layer_refs(root_layer)

        log.info(f"Export of USD node tree {tree.name_full} finished")

        return {'FINISHED'}


class HDUSD_NODE_PT_usd_nodetree_tools(HdUSD_Panel):
    bl_label = "USD Tools"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Tool"

    @classmethod
    def poll(cls, context):
        tree = context.space_data.edit_tree
        return super().poll(context) and tree and tree.bl_idname == "hdusd.USDTree"

    def draw(self, context):
        layout = self.layout

        layout.operator(HDUSD_NODE_OP_export_usd_file.bl_idname, icon='EXPORT')
        layout.label(text="Replace current tree using")
        layout.operator(HDUSD_OP_usd_nodetree_add_basic_nodes.bl_idname,
                        text="Blender Scene", icon='SCENE_DATA').scene_source = "SCENE"
        layout.operator(HDUSD_OP_usd_nodetree_add_basic_nodes.bl_idname,
                        text="USD file", icon='FILE').scene_source = "USD_FILE"


class HDUSD_NODE_PT_usd_nodetree_dev(HdUSD_ChildPanel):
    bl_label = "Dev"
    bl_parent_id = 'HDUSD_NODE_PT_usd_nodetree_tools'
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"

    @classmethod
    def poll(cls, context):
        return config.show_dev_settings

    def draw(self, context):
        layout = self.layout

        layout.operator(HDUSD_OP_usd_tree_node_print_stage.bl_idname)
        layout.operator(HDUSD_OP_usd_tree_node_print_root_layer.bl_idname)
