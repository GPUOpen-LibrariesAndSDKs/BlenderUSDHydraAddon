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
import MaterialX as mx
import traceback

import bpy
from bpy_extras.io_utils import ExportHelper

from pathlib import Path
from . import HdUSD_Panel, HdUSD_ChildPanel, HdUSD_Operator
from ..mx_nodes.node_tree import MxNodeTree, NODE_LAYER_SEPARATION_WIDTH
from ..mx_nodes.nodes.base_node import is_mx_node_valid
from ..utils import get_temp_file, pass_node_reroute, title_str
from ..utils import mx as mx_utils
from .. import config

from ..utils import logging
log = logging.Log(tag='ui.mx_nodes')


class HDUSD_MATERIAL_PT_context(HdUSD_Panel):
    bl_label = ""
    bl_context = "material"
    bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        if context.active_object and context.active_object.type == 'GPENCIL':
            return False
        else:
            return (context.material or context.object) and super().poll(context)

    def draw(self, context):
        layout = self.layout

        material = context.material
        object = context.object
        slot = context.material_slot
        space = context.space_data

        if object:
            is_sortable = len(object.material_slots) > 1
            rows = 1
            if is_sortable:
                rows = 4

            row = layout.row()

            row.template_list("MATERIAL_UL_matslots", "", object, "material_slots", object,
                              "active_material_index", rows=rows)

            col = row.column(align=True)
            col.operator("object.material_slot_add", icon='ADD', text="")
            col.operator("object.material_slot_remove", icon='REMOVE', text="")

            col.menu("MATERIAL_MT_context_menu", icon='DOWNARROW_HLT', text="")

            if is_sortable:
                col.separator()

                col.operator("object.material_slot_move", icon='TRIA_UP', text="").direction = 'UP'
                col.operator("object.material_slot_move", icon='TRIA_DOWN', text="").direction = 'DOWN'

            if object.mode == 'EDIT':
                row = layout.row(align=True)
                row.operator("object.material_slot_assign", text="Assign")
                row.operator("object.material_slot_select", text="Select")
                row.operator("object.material_slot_deselect", text="Deselect")

        split = layout.split(factor=0.65)

        if object:
            split.template_ID(object, "active_material", new="hdusd.material_duplicate_mat_mx_node_tree")
            row = split.row()

            if slot:
                row.prop(slot, "link", text="")
            else:
                row.label()
        elif material:
            split.template_ID(space, "pin_id")
            split.separator()


class HDUSD_MATERIAL_PT_preview(HdUSD_Panel):
    bl_label = "Preview"
    bl_context = "material"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.material and super().poll(context)

    def draw(self, context):
        self.layout.template_preview(context.material)


class HDUSD_MATERIAL_OP_new_mx_node_tree(bpy.types.Operator):
    """Create new MaterialX node tree for selected material"""
    bl_idname = "hdusd.material_new_mx_node_tree"
    bl_label = "New"

    def execute(self, context):
        mat = context.material
        mx_node_tree = bpy.data.node_groups.new(f"MX_{mat.name}", type=MxNodeTree.bl_idname)
        mx_node_tree.create_basic_nodes()

        mat.hdusd.mx_node_tree = mx_node_tree
        return {"FINISHED"}


class HDUSD_MATERIAL_OP_duplicate_mat_mx_node_tree(bpy.types.Operator):
    """Create duplicates of Material and MaterialX node tree for selected material"""
    bl_idname = "hdusd.material_duplicate_mat_mx_node_tree"
    bl_label = ""

    def execute(self, context):
        bpy.ops.material.new()
        bpy.ops.hdusd.material_duplicate_mx_node_tree()
        return {"FINISHED"}


class HDUSD_MATERIAL_OP_duplicate_mx_node_tree(bpy.types.Operator):
    """Create duplicate of MaterialX node tree for selected material"""
    bl_idname = "hdusd.material_duplicate_mx_node_tree"
    bl_label = ""

    def execute(self, context):
        mat = context.object.active_material
        mx_node_tree = mat.hdusd.mx_node_tree

        if mx_node_tree:
            mat.hdusd.mx_node_tree = mx_node_tree.copy()

        return {"FINISHED"}


class HDUSD_MATERIAL_OP_convert_shader_to_mx(bpy.types.Operator):
    """Converts standard shader node tree to MaterialX node tree for selected material"""
    bl_idname = "hdusd.material_convert_shader_to_mx"
    bl_label = "Convert to MaterialX"

    def execute(self, context):
        if not context.material.hdusd.convert_shader_to_mx(context.object):
            return {'CANCELLED'}

        return {"FINISHED"}


class HDUSD_MATERIAL_OP_link_mx_node_tree(bpy.types.Operator):
    """Link MaterialX node tree to selected material"""
    bl_idname = "hdusd.material_link_mx_node_tree"
    bl_label = ""

    mx_node_tree_name: bpy.props.StringProperty(default="")

    def execute(self, context):
        context.material.hdusd.mx_node_tree = bpy.data.node_groups[self.mx_node_tree_name]
        return {"FINISHED"}


class HDUSD_MATERIAL_OP_unlink_mx_node_tree(bpy.types.Operator):
    """Unlink MaterialX node tree from selected material"""
    bl_idname = "hdusd.material_unlink_mx_node_tree"
    bl_label = ""

    def execute(self, context):
        context.material.hdusd.mx_node_tree = None
        return {"FINISHED"}


class HDUSD_MATERIAL_MT_mx_node_tree(bpy.types.Menu):
    bl_idname = "HDUSD_MATERIAL_MT_mx_node_tree"
    bl_label = "MX Nodetree"

    def draw(self, context):
        layout = self.layout
        node_groups = bpy.data.node_groups

        for ng in node_groups:
            if ng.bl_idname != 'hdusd.MxNodeTree':
                continue

            row = layout.row()
            row.enabled = bool(ng.output_node)
            op = row.operator(HDUSD_MATERIAL_OP_link_mx_node_tree.bl_idname,
                              text=ng.name, icon='MATERIAL')
            op.mx_node_tree_name = ng.name


class HDUSD_MATERIAL_PT_material(HdUSD_Panel):
    bl_label = ""
    bl_context = "material"

    @classmethod
    def poll(cls, context):
        return context.material and super().poll(context)

    def draw(self, context):
        mat_hdusd = context.material.hdusd
        layout = self.layout

        split = layout.row(align=True).split(factor=0.4)
        row = split.column()
        row.alignment = 'RIGHT'
        row.label(text="MaterialX")
        row = split.row()
        row = row.row(align=True)
        row.menu(HDUSD_MATERIAL_MT_mx_node_tree.bl_idname, text="", icon='MATERIAL')

        if mat_hdusd.mx_node_tree:
            row.prop(mat_hdusd.mx_node_tree, 'name', text="")
            row.operator(HDUSD_MATERIAL_OP_convert_shader_to_mx.bl_idname, icon='FILE_TICK', text="")
            row.operator(HDUSD_MATERIAL_OP_duplicate_mx_node_tree.bl_idname, icon='DUPLICATE')
            row.operator(HDUSD_MATERIAL_OP_unlink_mx_node_tree.bl_idname, icon='X')

        else:
            row.operator(HDUSD_MATERIAL_OP_convert_shader_to_mx.bl_idname, icon='FILE_TICK', text="Convert")
            row.operator(HDUSD_MATERIAL_OP_new_mx_node_tree.bl_idname, icon='ADD', text="")

    def draw_header(self, context):
        layout = self.layout
        layout.label(text=f"Material: {context.material.name}")


class HDUSD_MATERIAL_OP_link_mx_node(bpy.types.Operator):
    """Link MaterialX node"""
    bl_idname = "hdusd.material_link_mx_node"
    bl_label = ""

    new_node_name: bpy.props.StringProperty()
    input_num: bpy.props.IntProperty()
    current_node_name: bpy.props.StringProperty()

    def execute(self, context):
        layout = self.layout

        node_tree = context.material.hdusd.mx_node_tree
        current_node = context.material.hdusd.mx_node_tree.nodes[self.current_node_name]

        input = current_node.inputs[self.input_num]
        link = next((link for link in input.links), None) if input.is_linked else None
        linked_node_name = link.from_node.bl_idname if link else None

        if linked_node_name:
            if linked_node_name != self.new_node_name:
                bpy.ops.hdusd.material_remove_node(input_node_name=link.from_node.name)
            else:
                return {"FINISHED"}

        new_node = node_tree.nodes.new(self.new_node_name)
        new_node.location = (current_node.location[0] - NODE_LAYER_SEPARATION_WIDTH,
                            current_node.location[1])
        node_tree.links.new(new_node.outputs[0], current_node.inputs[self.input_num])

        return {"FINISHED"}


class HDUSD_MATERIAL_OP_invoke_popup_input_nodes(bpy.types.Operator):
    """Open panel with nodes to link"""
    bl_idname = "hdusd.material_invoke_popup_input_nodes"
    bl_label = ""

    input_num: bpy.props.IntProperty()
    current_node_name: bpy.props.StringProperty()

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self, width=600)

    def draw(self, context):
        from ..mx_nodes.nodes import mx_node_classes

        MAX_COLUMN_ITEMS = 34

        split = self.layout.split()
        cat = ""
        i = 0
        col = None
        for cls in mx_node_classes:
            if cls.category in ("PBR", "material"):
                continue

            if not col or i >= MAX_COLUMN_ITEMS:
                i = 0
                col = split.column()
                col.emboss = 'PULLDOWN_MENU'

            if cat != cls.category:
                cat = cls.category
                col.label(text=title_str(cat), icon='NODE')
                i += 1

            row = col.row()
            row.alignment = 'LEFT'
            op = row.operator(HDUSD_MATERIAL_OP_link_mx_node.bl_idname, text=cls.bl_label)
            op.new_node_name = cls.bl_idname
            op.input_num = self.input_num
            op.current_node_name = self.current_node_name
            i += 1

        input = context.material.hdusd.mx_node_tree.nodes[self.current_node_name].inputs[self.input_num]
        if input.is_linked:
            link = input.links[0]

            col = split.column()
            col.emboss = 'PULLDOWN_MENU'
            col.label(text="Link")

            row = col.row()
            row.alignment = 'LEFT'
            op = row.operator(HDUSD_MATERIAL_OP_remove_node.bl_idname)
            op.input_node_name = link.from_node.name

            row = col.row()
            row.alignment = 'LEFT'
            op = row.operator(HDUSD_MATERIAL_OP_disconnect_node.bl_idname)
            op.output_node_name = link.to_node.name
            op.input_num = self.input_num


class HDUSD_MATERIAL_OP_invoke_popup_shader_nodes(bpy.types.Operator):
    """Open panel with shader nodes to link"""
    bl_idname = "hdusd.material_invoke_popup_shader_nodes"
    bl_label = ""

    input_num: bpy.props.IntProperty()
    new_node_name: bpy.props.StringProperty()

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self, width=300)

    def draw(self, context):
        from ..mx_nodes.nodes import mx_node_classes

        split = self.layout.split()
        col = split.column()
        col.emboss = 'PULLDOWN_MENU'
        col.label(text="PBR", icon='NODE')

        output_node = context.material.hdusd.mx_node_tree.output_node
        for cls in mx_node_classes:
            if cls.category != "PBR":
                continue

            row = col.row()
            row.alignment = 'LEFT'
            op = row.operator(HDUSD_MATERIAL_OP_link_mx_node.bl_idname, text=cls.bl_label)
            op.new_node_name = cls.bl_idname
            op.input_num = self.input_num
            op.current_node_name = output_node.name

        input = output_node.inputs[self.input_num]
        if input.is_linked:
            link = input.links[0]

            col = split.column()
            col.emboss = 'PULLDOWN_MENU'
            col.label(text="Link")

            row = col.row()
            row.alignment = 'LEFT'
            op = row.operator(HDUSD_MATERIAL_OP_remove_node.bl_idname)
            op.input_node_name = link.from_node.name

            row = col.row()
            row.alignment = 'LEFT'
            op = row.operator(HDUSD_MATERIAL_OP_disconnect_node.bl_idname)
            op.output_node_name = link.to_node.name
            op.input_num = self.input_num


class HDUSD_MATERIAL_OP_remove_node(bpy.types.Operator):
    """Remove linked node"""
    bl_idname = "hdusd.material_remove_node"
    bl_label = "Remove"

    input_node_name: bpy.props.StringProperty()

    def remove_nodes(self, context, node):
        for input in node.inputs:
            if input.is_linked:
                for link in input.links:
                    self.remove_nodes(context, link.from_node)

        context.material.hdusd.mx_node_tree.nodes.remove(node)

    def execute(self, context):
        node_tree = context.material.hdusd.mx_node_tree
        input_node = node_tree.nodes[self.input_node_name]

        self.remove_nodes(context, input_node)

        return {'FINISHED'}


class HDUSD_MATERIAL_OP_disconnect_node(bpy.types.Operator):
    """Disconnect linked node"""
    bl_idname = "hdusd.material_disconnect_node"
    bl_label = "Disconnect"

    output_node_name: bpy.props.StringProperty()
    input_num: bpy.props.IntProperty()

    def execute(self, context):
        node_tree = context.material.hdusd.mx_node_tree
        output_node = node_tree.nodes[self.output_node_name]

        links = output_node.inputs[self.input_num].links
        link = next((link for link in links), None)
        if link:
            node_tree.links.remove(link)

        return {'FINISHED'}


class HDUSD_MATERIAL_PT_material_settings_surface(HdUSD_ChildPanel):
    bl_label = "surfaceshader"
    bl_parent_id = 'HDUSD_MATERIAL_PT_material'

    @classmethod
    def poll(cls, context):
        return bool(context.material.hdusd.mx_node_tree)

    def draw(self, context):
        layout = self.layout

        node_tree = context.material.hdusd.mx_node_tree
        output_node = node_tree.output_node
        if not output_node:
            layout.label(text="No output node")
            return

        input = output_node.inputs[self.bl_label]
        link = next((link for link in input.links if link.is_valid), None)

        split = layout.split(factor=0.4)
        row = split.row(align=True)
        row.alignment = 'RIGHT'
        row.label(text='Surface')

        row = split.row(align=True)
        box = row.box()
        box.scale_x = 0.7
        box.scale_y = 0.5
        op = box.operator(HDUSD_MATERIAL_OP_invoke_popup_shader_nodes.bl_idname, icon='HANDLETYPE_AUTO_CLAMP_VEC')
        op.input_num = output_node.inputs.find(self.bl_label)

        if link and is_mx_node_valid(link.from_node):
            row.prop(link.from_node, 'name', text="")
        else:
            box = row.box()
            box.scale_y = 0.5
            box.label(text='None')

        row.label(icon='BLANK1')

        if not link:
            layout.label(text="No input node")
            return

        if not is_mx_node_valid(link.from_node):
            layout.label(text="Unsupported node")
            return

        link = pass_node_reroute(link)
        if not link:
            return

        layout.separator()

        link.from_node.draw_node_view(context, layout)


class HDUSD_MATERIAL_PT_material_settings_displacement(HdUSD_ChildPanel):
    bl_label = "displacementshader"
    bl_parent_id = 'HDUSD_MATERIAL_PT_material'

    @classmethod
    def poll(cls, context):
        return bool(context.material.hdusd.mx_node_tree)

    def draw(self, context):
        layout = self.layout

        node_tree = context.material.hdusd.mx_node_tree
        output_node = node_tree.output_node
        if not output_node:
            layout.label(text="No output node")
            return

        input = output_node.inputs[self.bl_label]
        link = next((link for link in input.links if link.is_valid), None)

        split = layout.split(factor=0.4)
        row = split.row(align=True)
        row.alignment = 'RIGHT'
        row.label(text='Displacement')

        row = split.row(align=True)
        box = row.box()
        box.scale_x = 0.7
        box.scale_y = 0.5
        op = box.operator(HDUSD_MATERIAL_OP_invoke_popup_shader_nodes.bl_idname, icon='HANDLETYPE_AUTO_CLAMP_VEC')
        op.input_num = output_node.inputs.find(self.bl_label)

        if link and is_mx_node_valid(link.from_node):
            row.prop(link.from_node, 'name', text="")
        else:
            box = row.box()
            box.scale_y = 0.5
            box.label(text='None')

        row.label(icon='BLANK1')

        if not link:
            layout.label(text="No input node")
            return

        if not is_mx_node_valid(link.from_node):
            layout.label(text="Unsupported node")
            return

        link = pass_node_reroute(link)
        if not link:
            return

        layout.separator()

        link.from_node.draw_node_view(context, layout)


class HDUSD_MATERIAL_PT_output_node(HdUSD_ChildPanel):
    bl_label = ""
    bl_parent_id = 'HDUSD_MATERIAL_PT_material'

    @classmethod
    def poll(cls, context):
        return not bool(context.material.hdusd.mx_node_tree)

    def draw(self, context):
        layout = self.layout

        node_tree = context.material.node_tree

        output_node = context.material.hdusd.output_node
        if not output_node:
            layout.label(text="No output node")
            return

        input = output_node.inputs[self.bl_label]
        layout.template_node_view(node_tree, output_node, input)


class HDUSD_MATERIAL_PT_output_surface(HDUSD_MATERIAL_PT_output_node):
    bl_label = "Surface"


class HDUSD_MATERIAL_PT_output_displacement(HDUSD_MATERIAL_PT_output_node):
    bl_label = "Displacement"
    bl_options = {'DEFAULT_CLOSED'}


class HDUSD_MATERIAL_PT_output_volume(HDUSD_MATERIAL_PT_output_node):
    bl_label = "Volume"
    bl_options = {'DEFAULT_CLOSED'}


class HDUSD_MATERIAL_OP_export_mx_file(HdUSD_Operator, ExportHelper):
    bl_idname = "hdusd.material_export_mx_file"
    bl_label = "Export MaterialX"
    bl_description = "Export material as MaterialX node tree to .mtlx file"

    # region properties
    filename_ext = ".mtlx"

    filepath: bpy.props.StringProperty(
        name="File Path",
        description="File path used for exporting material as MaterialX node tree to .mtlx file",
        maxlen=1024,
        subtype="FILE_PATH"
    )
    filter_glob: bpy.props.StringProperty(
        default="*.mtlx",
        options={'HIDDEN'},
    )
    is_export_deps: bpy.props.BoolProperty(
        name="Include dependencies",
        description="Export used MaterialX dependencies",
        default=False
    )
    is_export_textures: bpy.props.BoolProperty(
        name="Export bound textures",
        description="Export bound textures to corresponded folder",
        default=True
    )
    is_clean_texture_folder: bpy.props.BoolProperty(
        name="Сlean texture folder",
        description="Сlean texture folder before export",
        default=False
    )
    is_clean_deps_folders: bpy.props.BoolProperty(
        name="Сlean dependencies folders",
        description="Сlean MaterialX dependencies folders before export",
        default=False
    )
    texture_dir_name: bpy.props.StringProperty(
        name="Folder name",
        description="Texture folder name used for exporting files",
        default='textures',
        maxlen=1024,
    )
    is_create_new_folder: bpy.props.BoolProperty(
        name="Create new folder",
        description="Create new folder for material",
        default=True
    )
    # endregion

    def execute(self, context):
        hdusd_prop = context.material.hdusd

        if not hdusd_prop.convert_shader_to_mx():
            return {'CANCELLED'}

        doc = context.material.hdusd.export(None)
        if not doc:
            return {'CANCELLED'}

        if self.is_create_new_folder:
            self.filepath = str(Path(self.filepath).parent / context.material.name_full / Path(self.filepath).name)

        mx_utils.export_mx_to_file(doc, self.filepath,
                                   mx_node_tree=hdusd_prop.mx_node_tree,
                                   is_export_deps=self.is_export_deps,
                                   is_export_textures=self.is_export_textures,
                                   texture_dir_name=self.texture_dir_name,
                                   is_clean_texture_folder=self.is_clean_texture_folder,
                                   is_clean_deps_folders=self.is_clean_deps_folders)

        bpy.data.node_groups.remove(hdusd_prop.mx_node_tree)
        return {'FINISHED'}

    def draw(self, context):
        self.layout.prop(self, 'is_create_new_folder')
        self.layout.prop(self, 'is_export_deps')

        col = self.layout.column(align=False)
        col.prop(self, 'is_export_textures')

        row = col.row()
        row.enabled = self.is_export_textures
        row.prop(self, 'texture_dir_name', text='')


class HDUSD_MATERIAL_OP_export_mx_console(HdUSD_Operator):
    bl_idname = "hdusd.material_export_mx_console"
    bl_label = "Export MaterialX to Console"
    bl_description = "Export material as MaterialX node tree to console"

    def execute(self, context):
        doc = context.material.hdusd.export(context.object)
        if not doc:
            return {'CANCELLED'}

        print(mx.writeToXmlString(doc))
        return {'FINISHED'}


class HDUSD_MATERIAL_PT_tools(HdUSD_Panel):
    bl_label = "MaterialX Tools"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Tool"

    @classmethod
    def poll(cls, context):
        tree = context.space_data.edit_tree
        return super().poll(context) and tree and \
               tree.bl_idname == bpy.types.ShaderNodeTree.__name__

    def draw(self, context):
        layout = self.layout

        layout.operator(HDUSD_MATERIAL_OP_convert_shader_to_mx.bl_idname, icon='FILE_TICK')
        layout.operator(HDUSD_MATERIAL_OP_export_mx_file.bl_idname, text="Export MaterialX to file", icon='EXPORT')


class HDUSD_MATERIAL_PT_dev(HdUSD_ChildPanel):
    bl_label = "Dev"
    bl_parent_id = 'HDUSD_MATERIAL_PT_tools'
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"

    @classmethod
    def poll(cls, context):
        return config.show_dev_settings

    def draw(self, context):
        layout = self.layout

        layout.operator(HDUSD_MATERIAL_OP_export_mx_console.bl_idname)


def depsgraph_update(depsgraph):
    context = bpy.context
    mx_node_tree = None
    if hasattr(context, 'object') and context.object and context.object.active_material:
        mx_node_tree = context.object.active_material.hdusd.mx_node_tree

    # trying to show MaterialX area with node tree or Shader area
    screen = context.screen
    if not hasattr(screen, 'areas'):
        return

    if mx_node_tree:
        for area in screen.areas:
            if area.ui_type not in ('hdusd.MxNodeTree', 'ShaderNodeTree'):
                continue

            space = next(s for s in area.spaces if s.type == 'NODE_EDITOR')
            if not space.pin:
                bpy.types.NODE_HT_header.remove(mx_utils.update_material_iu)
                area.ui_type = 'hdusd.MxNodeTree'
                space.node_tree = mx_node_tree
                bpy.types.NODE_HT_header.append(mx_utils.update_material_iu)

    else:
        for area in screen.areas:
            if area.ui_type != 'hdusd.MxNodeTree':
                continue

            space = next(s for s in area.spaces if s.type == 'NODE_EDITOR')
            if not space.pin:
                area.ui_type = 'ShaderNodeTree'
