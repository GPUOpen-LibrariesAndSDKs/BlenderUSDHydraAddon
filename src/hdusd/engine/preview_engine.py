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

from .engine import Engine
from .final_engine import FinalEngine

from ..utils import logging
log = logging.Log(tag='PreviewEngine')


class PreviewEngine(FinalEngine):
    TYPE = 'PREVIEW'

    def render(self, scene):
        return

    def sync(self, depsgraph):
        scene = depsgraph.scene
        settings_scene = bpy.context.scene

        resolution = (scene.render.resolution_x, scene.render.resolution_y)

        return
