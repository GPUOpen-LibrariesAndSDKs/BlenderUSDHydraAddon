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
from nodeitems_utils import (
    NodeCategory,
    NodeItem,
    register_node_categories,
    unregister_node_categories,
)
from nodeitems_builtins import (
    ShaderNodeCategory,
)

from ..utils import logging
log = logging.LogOnce("bl_nodes")


class HdUSD_CompatibleShaderNodeCategory(NodeCategory):
    """ Appear with an active USD plugin in Material shader editor only """
    @classmethod
    def poll(cls, context):
        return context.scene.render.engine == "HdUSD"\
               and context.space_data.tree_type == 'ShaderNodeTree'


# add nodes here once they are supported
node_categories = [
    HdUSD_CompatibleShaderNodeCategory('HDUSD_SHADER_NODE_CATEGORY_INPUT', "Input", items=[
        NodeItem('ShaderNodeRGB'),
        NodeItem('ShaderNodeValue'),
    ], ),
    HdUSD_CompatibleShaderNodeCategory('HDUSD_SHADER_NODE_CATEGORY_OUTPUT', "Output", items=[
        NodeItem('ShaderNodeOutputMaterial'),
    ], ),
    HdUSD_CompatibleShaderNodeCategory('HDUSD_SHADER_NODE_CATEGORY_SHADERS', "Shader", items=[
        NodeItem('ShaderNodeBsdfDiffuse'),
        NodeItem('ShaderNodeBsdfGlass'),
        NodeItem('ShaderNodeEmission'),
        NodeItem('ShaderNodeBsdfPrincipled'),
    ]),
    HdUSD_CompatibleShaderNodeCategory('HDUSD_SHADER_NODE_CATEGORY_TEXTURE', "Texture", items=[
        NodeItem('ShaderNodeTexImage'),
    ], ),
    HdUSD_CompatibleShaderNodeCategory('HDUSD_SHADER_NODE_CATEGORY_COLOR', "Color", items=[
        NodeItem('ShaderNodeInvert'),
        NodeItem('ShaderNodeMixRGB'),
    ], ),
    HdUSD_CompatibleShaderNodeCategory('HDUSD_SHADER_NODE_CATEGORY_CONVERTER', "Converter", items=[
        NodeItem('ShaderNodeMixRGB'),
    ], ),
    HdUSD_CompatibleShaderNodeCategory('HDUSD_SHADER_NODE_CATEGORY_VECTOR', "Vector", items=[
        NodeItem('ShaderNodeNormalMap'),
    ], ),
    HdUSD_CompatibleShaderNodeCategory('HDUSD_SHADER_NODE_CATEGORY_LAYOUT', "Layout", items=[
        NodeItem('NodeReroute'),
        NodeItem('NodeFrame'),
    ], ),
]


# some nodes are hidden from plugins by Cycles itself(like Material Output), some we could not support.
# thus we'll hide 'em all to show only selected set of supported Blender nodes
# custom HdUSD_CompatibleShaderNodeCategory will be used instead
def hide_cycles_and_eevee_poll(method):
    @classmethod
    def func(cls, context):
        return not context.scene.render.engine == 'HdUSD' and method(context)
    return func


old_shader_node_category_poll = None


def register():
    # hide Cycles/Eevee menu
    global old_shader_node_category_poll
    old_shader_node_category_poll = ShaderNodeCategory.poll
    ShaderNodeCategory.poll = hide_cycles_and_eevee_poll(ShaderNodeCategory.poll)

    # use custom menu
    register_node_categories("HDUSD_NODES", node_categories)


def unregister():
    # restore Cycles/Eevee menu
    if old_shader_node_category_poll and ShaderNodeCategory.poll is not old_shader_node_category_poll:
        ShaderNodeCategory.poll = old_shader_node_category_poll

    # remove custom menu
    unregister_node_categories("HDUSD_NODES")
