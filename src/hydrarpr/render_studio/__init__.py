# **********************************************************************
# Copyright 2023 Advanced Micro Devices, Inc
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
# ********************************************************************
import bpy
from pxr import Plug


def register():
    usd_plugin = Plug.Registry().GetPluginWithName('RenderStudioResolver')
    usd_plugin.Load()
    
    from . import resolver, ui, properties, operators
    properties.register()
    operators.register()
    ui.register()

    bpy.app.handlers.depsgraph_update_post.append(resolver.on_depsgraph_update_post)


def unregister():
    from . import resolver, ui, properties, operators

    if resolver.on_depsgraph_update_post in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(resolver.on_depsgraph_update_post)

    if bpy.context.collection.resolver.is_connected:
        bpy.context.collection.resolver.disconnect()

    ui.unregister()
    operators.unregister()
    properties.unregister()
