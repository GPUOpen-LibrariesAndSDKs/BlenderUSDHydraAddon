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

from ...utils import title_str, code_str, LIBS_DIR
from ...utils import mx as mx_utils
from . import log


class MxNodeInputSocket(bpy.types.NodeSocket):
    bl_idname = 'hdusd.MxNodeInputSocket'
    bl_label = "MX Input Socket"

    @staticmethod
    def get_color(type_name):
        return (0.78, 0.78, 0.16, 1.0) if mx_utils.is_shader_type(type_name) else \
               (0.16, 0.78, 0.16, 1.0)

    def draw(self, context, layout, node, text):
        nd = node.prop.nodedef()
        nd_input = nd.getInput(self.name)
        nd_type = nd_input.getType()

        uiname = mx_utils.get_attr(nd_input, 'uiname', title_str(nd_input.getName()))
        if nd.getName() == "ND_rpr_uber_surfaceshader":
            # special case for ND_rpr_uber_surfaceshader
            uifolder = mx_utils.get_attr(nd_input, 'uifolder')
            uiname = f"{uifolder} {uiname}"

        if self.is_linked or mx_utils.is_shader_type(nd_type) or nd_input.getValue() is None:
            uitype = title_str(nd_type)
            if uiname.lower() == uitype.lower():
                layout.label(text=uitype)
            else:
                layout.label(text=f"{uiname}: {uitype}")
        else:
            layout.prop(node.prop, MxNodeDef._input_prop_name(self.name), text=uiname)

    def draw_color(self, context, node):
        return self.get_color(node.prop.nodedef().getInput(self.name).getType())


class MxNodeOutputSocket(bpy.types.NodeSocket):
    bl_idname = 'hdusd.MxNodeOutputSocket'
    bl_label = "MX Output Socket"

    def draw(self, context, layout, node, text):
        nd = node.prop.nodedef()
        mx_output = nd.getOutput(self.name)
        uiname = mx_utils.get_attr(mx_output, 'uiname', title_str(mx_output.getName()))
        uitype = title_str(mx_output.getType())
        if uiname.lower() == uitype.lower() or len(nd.getOutputs()) == 1:
            layout.label(text=uitype)
        else:
            layout.label(text=f"{uiname}: {uitype}")

    def draw_color(self, context, node):
        return MxNodeInputSocket.get_color(node.prop.nodedef().getOutput(self.name).getType())


class MxNodeDef(bpy.types.PropertyGroup):
    _file_path: str
    _nodedef_name: str
    _node_name: str

    _nodedef: mx.NodeDef = None

    @classmethod
    def nodedef(cls):
        if cls._nodedef is None:
            doc = mx.createDocument()
            mx.readFromXmlFile(doc, str(LIBS_DIR / cls._file_path))
            cls._nodedef = doc.getNodeDef(cls._nodedef_name)

        return cls._nodedef

    @staticmethod
    def _param_prop_name(name):
        return 'p_' + name

    @staticmethod
    def _input_prop_name(name):
        return 'in_' + name

    def update_prop(self, context):
        nodetree = self.id_data
        nodetree.update_()

    def get_input(self, name):
        return getattr(self, self._input_prop_name(name))

    def set_input(self, name, value):
        setattr(self, self._input_prop_name(name), value)

    def get_param(self, name):
        return getattr(self, self._param_prop_name(name))

    def set_param(self, name, value):
        setattr(self, self._param_prop_name(name), value)

    def get_nodedef_input(self, name):
        return self.nodedef().getInput(name)

    def get_nodedef_output(self, name):
        return self.nodedef().getOutput(name)


class MxNode(bpy.types.ShaderNode):
    """Base node from which all MaterialX nodes will be made"""
    bl_compatibility = {'HdUSD'}
    bl_idname = 'hdusd.'
    # bl_icon = 'MATERIAL'

    bl_label = ""
    bl_description = ""
    bl_width_default = 200

    _data_types = ()    # list of available types from nodedefs
    _ui_folders = ()    # list of ui folders mentioned in nodedef
    category = ""
    data_type = None

    @staticmethod
    def _folder_prop_name(name):
        return 'f_' + code_str(name.lower())

    @staticmethod
    def _nodedef_prop_name(name):
        return 'nd_' + name

    def init(self, context):
        def init_():
            nodedef = self.prop.nodedef()

            for mx_input in nodedef.getInputs():
                if mx_input.getAttribute('uniform') == 'true':
                    continue

                self.create_input(mx_input)

            for mx_output in nodedef.getOutputs():
                self.create_output(mx_output)

            if self._ui_folders:
                self.ui_folders_update(context)

        nodetree = self.id_data
        nodetree.no_update_call(init_)

    def draw_buttons(self, context, layout):
        if len(self._data_types) > 1:
            layout.prop(self, 'data_type')

        nodedef = self.prop.nodedef()

        if self._ui_folders:
            col = layout.column(align=True)
            r = None
            for i, f in enumerate(self._ui_folders):
                if i % 3 == 0:  # putting 3 buttons per row
                    r = col.row(align=True)
                r.prop(self, self._folder_prop_name(f), toggle=True)

        for mx_input in mx_utils.get_nodedef_inputs(nodedef, True):
            f = mx_input.getAttribute('uifolder')
            if f and not getattr(self, self._folder_prop_name(f)):
                continue

            layout.prop(self.prop, MxNodeDef._input_prop_name(mx_input.getName()))

        for mx_param in nodedef.getParameters():
            f = mx_param.getAttribute('uifolder')
            if f and not getattr(self, self._folder_prop_name(f)):
                continue

            name = mx_param.getName()
            if self.category in ("texture2d", "texture3d") and mx_param.getType() == 'filename':
                split = layout.row(align=True).split(factor=0.25, align=True)
                col = split.column()
                col.label(text=mx_param.getAttribute('uiname') if mx_param.hasAttribute('uiname')
                          else title_str(name))
                col = split.column()
                col.template_ID(self.prop, MxNodeDef._param_prop_name(name),
                                open="image.open", new="image.new")

            else:
                layout.prop(self.prop, MxNodeDef._param_prop_name(name))

    # COMPUTE FUNCTION
    def compute(self, out_key, **kwargs):
        log("compute", self, out_key)

        doc = kwargs['doc']
        nodedef = self.prop.nodedef()
        nd_output = self.get_nodedef_output(out_key)

        values = []
        for in_key in range(len(self.inputs)):
            nd_input = self.get_nodedef_input(in_key)
            f = nd_input.getAttribute('uifolder')
            if f and not getattr(self, self._folder_prop_name(f)):
                continue

            values.append((in_key, self.get_input_value(in_key, **kwargs)))

        mx_nodegraph = mx_utils.get_nodegraph_by_node_path(doc, self.name, True)
        node_name = mx_utils.get_node_name_by_node_path(self.name)
        mx_node = mx_nodegraph.addNode(nodedef.getNodeString(), node_name, nd_output.getType())
        for in_key, val in values:
            nd_input = self.get_nodedef_input(in_key)
            nd_type = nd_input.getType()
            if not isinstance(val, mx.Node):
                if mx_utils.is_shader_type(nd_type):
                    continue

                nd_val = nd_input.getValue()
                if nd_val is None or mx_utils.is_value_equal(nd_val, val, nd_type):
                    continue

            mx_input = mx_node.addInput(nd_input.getName(), nd_type)
            mx_utils.set_param_value(mx_input, val, nd_type)

        for nd_param in nodedef.getParameters():
            f = nd_param.getAttribute('uifolder')
            if f and not getattr(self, self._folder_prop_name(f)):
                continue

            val = self.get_param_value(nd_param.getName())
            nd_type = nd_param.getType()
            if mx_utils.is_value_equal(nd_param.getValue(), val, nd_type):
                continue

            mx_param = mx_node.addParameter(nd_param.getName(), nd_type)
            mx_utils.set_param_value(mx_param, val, nd_type)

        return mx_node

    def _compute_node(self, node, out_key, **kwargs):
        doc = kwargs['doc']
        mx_nodegraph = mx_utils.get_nodegraph_by_node_path(doc, node.name)
        if mx_nodegraph:
            node_name = mx_utils.get_node_name_by_node_path(node.name)
            mx_node = mx_nodegraph.getNode(node_name)
            if mx_node:
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

        return self._compute_node(link.from_node, link.from_socket.name, **kwargs)

    def get_input_value(self, in_key: [str, int], **kwargs):
        node = self.get_input_link(in_key, **kwargs)
        if node:
            return node

        return self.get_input_default(in_key)

    def get_input_default(self, in_key: [str, int]):
        return self.prop.get_input(self.inputs[in_key].identifier)

    def get_param_value(self, name):
        return self.prop.get_param(name)

    def get_input_param_value(self, name):
        return self.prop.get_input(name)

    def get_nodedef_input(self, in_key: [str, int]):
        return self.prop.get_nodedef_input(self.inputs[in_key].identifier)

    def get_nodedef_output(self, out_key: [str, int]):
        return self.prop.get_nodedef_output(self.outputs[out_key].identifier)

    def set_input_default(self, in_key, value):
        self.prop.set_input(self.inputs[in_key].identifier, value)

    def set_param_value(self, name, value):
        self.prop.set_param(name, value)

    @property
    def prop(self):
        return getattr(self, self._nodedef_prop_name(self.data_type))

    @classmethod
    def poll(cls, tree):
        return tree.bl_idname == 'hdusd.MxNodeTree'

    def ui_folders_update(self, context):
        for i, mx_input in enumerate(self.prop.nodedef().getInputs()):
            f = mx_input.getAttribute('uifolder')
            if f:
                self.inputs[i].hide = not getattr(self, self._folder_prop_name(f))

        nodetree = self.id_data
        nodetree.update_()

    def ui_folders_check(self):
        if not self._ui_folders:
            return

        for f in self._ui_folders:
            setattr(self, self._folder_prop_name(f), False)

        for in_key, mx_input in enumerate(self.prop.nodedef().getInputs()):
            f = mx_input.getAttribute('uifolder')
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

        self.ui_folders_update(None)

    def create_input(self, mx_input):
        return self.inputs.new(MxNodeInputSocket.bl_idname, mx_input.getName())

    def create_output(self, mx_output):
        return self.outputs.new(MxNodeOutputSocket.bl_idname, mx_output.getName())
