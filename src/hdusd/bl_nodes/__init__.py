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
from nodeitems_builtins import (
    ShaderNodeCategory,
)

from ..utils import logging
log = logging.Log("bl_nodes")


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
    # hide Cycles
    global old_shader_node_category_poll
    old_shader_node_category_poll = ShaderNodeCategory.poll
    ShaderNodeCategory.poll = hide_cycles_and_eevee_poll(ShaderNodeCategory.poll)


def unregister():
    if old_shader_node_category_poll and ShaderNodeCategory.poll is not old_shader_node_category_poll:
        ShaderNodeCategory.poll = old_shader_node_category_poll
