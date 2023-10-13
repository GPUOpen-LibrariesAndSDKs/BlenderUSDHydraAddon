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
from pxr import Plug


def register():
    usd_plugin = Plug.Registry().GetPluginWithName('RenderStudioResolver')
    usd_plugin.Load()

    from . import resolver, ui, operators

    resolver.register()
    operators.register()
    ui.register()


def unregister():
    from . import resolver, ui, operators

    ui.unregister()
    operators.unregister()
    resolver.unregister()
