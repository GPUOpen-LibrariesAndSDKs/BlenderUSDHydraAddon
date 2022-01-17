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

from ...utils import title_str, code_str, LIBS_DIR, pass_node_reroute, BLENDER_VERSION
from ...utils import mx as mx_utils
from . import log


class MxNodeInputSocket(bpy.types.NodeSocket):
    bl_idname = 'hdusd.MxNodeInputSocket'
    bl_label = "MX Input Socket"

    def draw(self, context, layout, node, text):
        if not is_mx_node_valid(node):
            return

        nd = node.nodedef
        nd_input = nd.getInput(self.name)
        nd_type = nd_input.getType()

        uiname = mx_utils.get_attr(nd_input, 'uiname', title_str(nd_input.getName()))
        is_prop_area = context.area.type == 'PROPERTIES'
        if self.is_linked or mx_utils.is_shader_type(nd_type) or nd_input.getValue() is None:
            uitype = title_str(nd_type)
            layout.label(text=uitype if uiname.lower() == uitype.lower() or is_prop_area else f"{uiname}: {uitype}")
        else:
            if nd_type == 'boolean':
                layout.use_property_split = False
                layout.alignment = 'LEFT'
            layout.prop(node, node._input_prop_name(self.name), text='' if is_prop_area else uiname)


    def draw_color(self, context, node):
        return mx_utils.get_socket_color(node.nodedef.getInput(self.name).getType()
                                         if is_mx_node_valid(node) else 'undefined')


class MxNodeOutputSocket(bpy.types.NodeSocket):
    bl_idname = 'hdusd.MxNodeOutputSocket'
    bl_label = "MX Output Socket"

    def draw(self, context, layout, node, text):
        if not is_mx_node_valid(node):
            return

        nd = node.nodedef
        mx_output = nd.getOutput(self.name)
        uiname = mx_utils.get_attr(mx_output, 'uiname', title_str(mx_output.getName()))
        uitype = title_str(mx_output.getType())
        if uiname.lower() == uitype.lower() or len(nd.getOutputs()) == 1:
            layout.label(text=uitype)
        else:
            layout.label(text=f"{uiname}: {uitype}")

    def draw_color(self, context, node):
        return mx_utils.get_socket_color(node.nodedef.getOutput(self.name).getType()
                                         if is_mx_node_valid(node) else 'undefined')


class MxNode(bpy.types.ShaderNode):
    """Base node from which all MaterialX nodes will be made"""
    _file_path: str
    bl_compatibility = {'HdUSD'}
    bl_idname = 'hdusd.'
    # bl_icon = 'MATERIAL'

    bl_label = ""
    bl_description = ""
    bl_width_default = 200

    _data_types = {}    # available types and nodedefs
    _ui_folders = ()    # list of ui folders mentioned in nodedef
    category = ""

    @classmethod
    def get_nodedef(cls, data_type):
        if not cls._data_types[data_type]['nd']:
            # loading nodedefs
            doc = mx.createDocument()
            search_path = mx.FileSearchPath(str(mx_utils.MX_LIBS_DIR))
            mx.readFromXmlFile(doc, str(LIBS_DIR / cls._file_path), searchPath=search_path)
            for val in cls._data_types.values():
                val['nd'] = doc.getNodeDef(val['nd_name'])

        return cls._data_types[data_type]['nd']

    @classmethod
    def get_nodedefs(cls):
        for data_type in cls._data_types.keys():
            yield cls.get_nodedef(data_type), data_type

    @property
    def nodedef(self):
        return self.get_nodedef(self.data_type)

    @property
    def mx_node_path(self):
        nd = self.nodedef
        if '/' in self.name or mx_utils.is_shader_type(nd.getOutputs()[0].getType()):
            return self.name

        return f"NG/{self.name}"

    def _folder_prop_name(self, name):
        return f"f_{code_str(name.lower())}"

    def _input_prop_name(self, name):
        return f"nd_{self.data_type}_in_{name}"

    def update_prop(self, context):
        nodetree = self.id_data
        nodetree.update_()

    def update_data_type(self, context):
        # updating names for inputs and outputs
        nodedef = self.nodedef
        for i, nd_input in enumerate(mx_utils.get_nodedef_inputs(nodedef, False)):
            self.inputs[i].name = nd_input.getName()
        for i, nd_output in enumerate(nodedef.getOutputs()):
            self.outputs[i].name = nd_output.getName()

    def init(self, context):
        def init_():
            nodedef = self.nodedef

            for nd_input in mx_utils.get_nodedef_inputs(nodedef, False):
                self.create_input(nd_input)

            for nd_output in nodedef.getOutputs():
                self.create_output(nd_output)

            if self._ui_folders:
                self.update_ui_folders(context)

        nodetree = self.id_data
        nodetree.no_update_call(init_)

    def draw_buttons(self, context, layout):
        is_prop_area = context.area.type == 'PROPERTIES'
        if len(self._data_types) > 1:
            layout1 = layout
            if is_prop_area:
                layout1 = layout1.split(factor=0.012, align=True)
                col = layout1.column()
                layout1 = layout1.column()
            layout1.prop(self, 'data_type')

        nodedef = self.nodedef

        if self._ui_folders:
            col = layout.column(align=True)
            r = None
            for i, f in enumerate(self._ui_folders):
                if i % 3 == 0:  # putting 3 buttons per row
                    col.use_property_split = False
                    col.use_property_decorate = False
                    r = col.row(align=True)
                r.prop(self, self._folder_prop_name(f), toggle=True)

        for nd_input in mx_utils.get_nodedef_inputs(nodedef, True):
            f = nd_input.getAttribute('uifolder')
            if f and not getattr(self, self._folder_prop_name(f)):
                continue

            name = nd_input.getName()
            if self.category in ("texture2d", "texture3d") and nd_input.getType() == 'filename':
                split = layout.row(align=True).split(factor=0.4 if is_prop_area else 0.25, align=True)
                col = split.column()
                col.alignment='RIGHT' if is_prop_area else 'EXPAND'
                col.label(text=nd_input.getAttribute('uiname') if nd_input.hasAttribute('uiname')
                          else title_str(name))
                col = split.column()
                col.template_ID(self, self._input_prop_name(name),
                                open="image.open", new="image.new")

            else:
                layout1 = layout
                if is_prop_area:
                    layout1 = layout1.split(factor=0.012, align=True)
                    col = layout1.column()
                    layout1 = layout1.column()
                layout1.prop(self, self._input_prop_name(name))

    def draw_node_view(self, context, layout):
        from ...ui.material import HDUSD_MATERIAL_OP_invoke_popup_input_nodes
        layout.use_property_split = True
        layout.use_property_decorate = True
        self.draw_buttons(context, layout)

        for i, socket_in in enumerate(self.inputs):
            nd = self.nodedef
            uiname = mx_utils.get_attr(nd.getInput(socket_in.name), 'uiname',
                                       title_str(nd.getInput(socket_in.name).getName()))
            if socket_in.is_linked:
                link = next((link for link in socket_in.links if link.is_valid), None)
                if not link:
                    continue

                link = pass_node_reroute(link)
                if not link or isinstance(link.from_node, bpy.types.NodeReroute):
                    continue

                split = layout.split(factor=0.4)
                split_1 = split.split(factor=0.4)

                row = split_1.row()
                row.use_property_split = False
                row.use_property_decorate = False
                row.alignment = 'LEFT'
                row.prop(socket_in, "show_expanded",
                         icon="DISCLOSURE_TRI_DOWN" if socket_in.show_expanded else "DISCLOSURE_TRI_RIGHT",
                         icon_only=True, emboss=False)
                row = split_1.row()
                row.alignment = 'RIGHT'
                row.label(text=uiname)
                row = split.row(align=True)
                row.use_property_decorate = False

                box = row.box()
                box.scale_x = 0.7
                box.scale_y = 0.5
                box.emboss = 'NONE_OR_STATUS' if BLENDER_VERSION >= "3.0" else 'UI_EMBOSS_NONE_OR_STATUS'

                op = box.operator(HDUSD_MATERIAL_OP_invoke_popup_input_nodes.bl_idname, icon='HANDLETYPE_AUTO_CLAMP_VEC')
                op.input_num = i
                op.current_node_name = self.name

                row.prop(link.from_node, 'name', text='')
                row.label(icon='BLANK1')

                if socket_in.show_expanded:
                    link.from_node.draw_node_view(context, layout)

            else:
                mx_input = self.nodedef.getInput(socket_in.name)
                f = mx_input.getAttribute('uifolder')
                is_draw = True
                if f:
                    if not getattr(self, self._folder_prop_name(f)):
                        is_draw = False

                if is_draw:
                    split = layout.split(factor=0.4)

                    row = split.row(align=True)
                    row.alignment = 'RIGHT'
                    row.label(text=uiname)
                    row = split.row(align=True)
                    box = row.box()
                    box.scale_x = 0.7
                    box.scale_y = 0.5

                    op = box.operator(HDUSD_MATERIAL_OP_invoke_popup_input_nodes.bl_idname,
                                      icon='HANDLETYPE_AUTO_CLAMP_VEC')
                    op.input_num = i
                    op.current_node_name = self.name

                    socket_in.draw(context, row, self, '')

    # COMPUTE FUNCTION
    def compute(self, out_key, **kwargs):
        log("compute", self, out_key)

        doc = kwargs['doc']
        nodedef = self.nodedef
        nd_output = self.get_nodedef_output(out_key)
        node_path = self.mx_node_path

        values = []
        for in_key in range(len(self.inputs)):
            nd_input = self.get_nodedef_input(in_key)
            f = nd_input.getAttribute('uifolder')
            if f and not getattr(self, self._folder_prop_name(f)):
                continue

            values.append((in_key, self.get_input_value(in_key, **kwargs)))

        mx_nodegraph = mx_utils.get_nodegraph_by_node_path(doc, node_path, True)
        node_name = mx_utils.get_node_name_by_node_path(node_path)
        mx_node = mx_nodegraph.addNode(nodedef.getNodeString(), node_name, nd_output.getType())

        for in_key, val in values:
            nd_input = self.get_nodedef_input(in_key)
            nd_type = nd_input.getType()

            if isinstance(val, mx.Node):
                mx_input = mx_node.addInput(nd_input.getName(), nd_type)
                mx_utils.set_param_value(mx_input, val, nd_type)
                continue

            if isinstance(val, tuple) and isinstance(val[0], mx.Node):
                # node with multioutput type
                in_node, in_nd_output = val
                mx_input = mx_node.addInput(nd_input.getName(), nd_type)
                mx_utils.set_param_value(mx_input, in_node, nd_type, in_nd_output)
                continue

            if mx_utils.is_shader_type(nd_type):
                continue

            nd_val = nd_input.getValue()
            if nd_val is None or mx_utils.is_value_equal(nd_val, val, nd_type):
                continue

            mx_input = mx_node.addInput(nd_input.getName(), nd_type)
            mx_utils.set_param_value(mx_input, val, nd_type)

        for nd_input in mx_utils.get_nodedef_inputs(nodedef, True):
            f = nd_input.getAttribute('uifolder')
            if f and not getattr(self, self._folder_prop_name(f)):
                continue

            val = self.get_param_value(nd_input.getName())
            nd_type = nd_input.getType()
            if mx_utils.is_value_equal(nd_input.getValue(), val, nd_type):
                continue

            mx_param = mx_node.addInput(nd_input.getName(), nd_type)
            mx_utils.set_param_value(mx_param, val, nd_type)

        if len(nodedef.getOutputs()) > 1:
            mx_node.setType('multioutput')
            return mx_node, nd_output

        return mx_node

    def _compute_node(self, node, out_key, **kwargs):
        # checking if node is already in nodegraph

        doc = kwargs['doc']
        node_path = node.mx_node_path
        mx_nodegraph = mx_utils.get_nodegraph_by_node_path(doc, node_path)
        if mx_nodegraph:
            node_name = mx_utils.get_node_name_by_node_path(node_path)
            mx_node = mx_nodegraph.getNode(node_name)
            if mx_node:
                if mx_node.getType() == 'multioutput':
                    nd_output = node.get_nodedef_output(out_key)
                    return mx_node, nd_output

                return mx_node

        return node.compute(out_key, **kwargs)

    def get_input_link(self, in_key: [str, int], **kwargs):
        """Returns linked parsed node or None if nothing is linked or not link is not valid"""

        socket_in = self.inputs[in_key]
        if not socket_in.links:
            return None

        link = socket_in.links[0]
        if not link.is_valid:
            log.error("Invalid link found", link, socket_in, self)

        link = pass_node_reroute(link)
        if not link:
            return None

        if not is_mx_node_valid(link.from_node):
            log.warn(f"Ignoring unsupported node {link.from_node.bl_idname}", link.from_node, link.from_node.id_data)
            return None

        return self._compute_node(link.from_node, link.from_socket.name, **kwargs)

    def get_input_value(self, in_key: [str, int], **kwargs):
        node = self.get_input_link(in_key, **kwargs)
        if node:
            return node

        return self.get_input_default(in_key)

    def get_input_default(self, in_key: [str, int]):
        return getattr(self, self._input_prop_name(self.inputs[in_key].name))

    def get_param_value(self, name):
        return getattr(self, self._input_prop_name(name))

    def get_nodedef_input(self, in_key: [str, int]):
        return self.nodedef.getInput(self.inputs[in_key].name)

    def get_nodedef_output(self, out_key: [str, int]):
        return self.nodedef.getOutput(self.outputs[out_key].name)

    def set_input_value(self, in_key, value):
        setattr(self, self._input_prop_name(self.inputs[in_key].name), value)

    def set_param_value(self, name, value):
        setattr(self, self._input_prop_name(name), value)

    @classmethod
    def poll(cls, tree):
        return tree.bl_idname == 'hdusd.MxNodeTree'

    def update_ui_folders(self, context):
        for i, nd_input in enumerate(mx_utils.get_nodedef_inputs(self.nodedef, False)):
            f = nd_input.getAttribute('uifolder')
            if f:
                self.inputs[i].hide = not getattr(self, self._folder_prop_name(f))

        nodetree = self.id_data
        nodetree.update_()

    def check_ui_folders(self):
        if not self._ui_folders:
            return

        for f in self._ui_folders:
            setattr(self, self._folder_prop_name(f), False)

        for in_key, nd_input in enumerate(mx_utils.get_nodedef_inputs(self.nodedef, False)):
            f = nd_input.getAttribute('uifolder')
            if not f:
                continue

            if self.inputs[in_key].links:
                setattr(self, self._folder_prop_name(f), True)
                continue

            nd_input = self.get_nodedef_input(in_key)
            val = self.get_input_default(in_key)
            nd_val = nd_input.getValue()
            if nd_val is None or mx_utils.is_value_equal(nd_val, val, nd_input.getType()):
                continue

            setattr(self, self._folder_prop_name(f), True)

        self.update_ui_folders(None)

    def create_input(self, nd_input):
        input = self.inputs.new(MxNodeInputSocket.bl_idname, f'in_{len(self.inputs)}')
        input.name = nd_input.getName()
        return input

    def create_output(self, mx_output):
        output = self.outputs.new(MxNodeOutputSocket.bl_idname, f'out_{len(self.outputs)}')
        output.name = mx_output.getName()
        return output


def is_mx_node_valid(node):
    # handle MaterialX 1.37 nodes
    return hasattr(node, 'nodedef')
