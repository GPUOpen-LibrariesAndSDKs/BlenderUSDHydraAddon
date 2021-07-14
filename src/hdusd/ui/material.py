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

import bpy
from bpy_extras.io_utils import ExportHelper

from . import HdUSD_Panel, HdUSD_ChildPanel, HdUSD_Operator
from ..mx_nodes.node_tree import MxNodeTree


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
            split.template_ID(object, "active_material", new="material.new")
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
        mx_node_tree.create_basic_nodes(
            'RPR_rpr_uberv2' if context.scene.hdusd.use_rpr_mx_nodes else 'PBR_standard_surface')
        mat.hdusd.mx_node_tree = mx_node_tree

        # trying to show MaterialX area with created node tree
        screen = context.screen
        area = next((a for a in screen.areas if a.ui_type == 'hdusd.MxNodeTree'), None)
        if not area:
            area = next((a for a in screen.areas if a.ui_type == 'ShaderNodeTree'), None)

        if area:
            area.ui_type = 'hdusd.MxNodeTree'
            space = next(s for s in area.spaces if s.type == 'NODE_EDITOR')
            space.node_tree = mx_node_tree

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
        col = split.column()
        col.alignment = 'RIGHT'
        col.label(text="MaterialX")
        col = split.column()
        row = col.row(align=True)
        col1 = row.column()
        col1.enabled = any(ng.bl_idname == 'hdusd.MxNodeTree' for ng in bpy.data.node_groups)
        col1.menu(HDUSD_MATERIAL_MT_mx_node_tree.bl_idname, text="", icon='MATERIAL')

        if mat_hdusd.mx_node_tree:
            row.prop(mat_hdusd.mx_node_tree, 'name', text="")
            row.operator(HDUSD_MATERIAL_OP_unlink_mx_node_tree.bl_idname, icon='X')

        else:
            row.operator(HDUSD_MATERIAL_OP_new_mx_node_tree.bl_idname, icon='ADD')

    def draw_header(self, context):
        layout = self.layout
        layout.label(text=f"Material: {context.material.name}")


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
    bl_label = "MaterialX Export to File"
    bl_description = "Export material as MaterialX node tree to .mtlx file"

    filename_ext = ".mtlx"
    filepath: bpy.props.StringProperty(
        name="File Path",
        description="File path used for exporting material as MaterialX node tree to .mtlx file",
        maxlen=1024, subtype="FILE_PATH"
    )
    filter_glob: bpy.props.StringProperty(default="*.mtlx", options={'HIDDEN'}, )

    def execute(self, context):
        doc = context.material.hdusd.export(context.object)
        if not doc:
            return {'CANCELLED'}

        mx.writeToXmlFile(doc, self.filepath)
        return {'FINISHED'}


class HDUSD_MATERIAL_OP_export_mx_console(HdUSD_Operator):
    bl_idname = "hdusd.material_export_mx_console"
    bl_label = "MaterialX Export to Console"
    bl_description = "Export material as MaterialX node tree to console"

    def execute(self, context):
        doc = context.material.hdusd.export(context.object)
        if not doc:
            return {'CANCELLED'}

        print(mx.writeToXmlString(doc))
        return {'FINISHED'}


class HDUSD_MATERIAL_PT_export_mx(HdUSD_Panel):
    bl_label = "MaterialX Export"
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

        layout.operator(HDUSD_MATERIAL_OP_export_mx_file.bl_idname)
        layout.operator(HDUSD_MATERIAL_OP_export_mx_console.bl_idname)
