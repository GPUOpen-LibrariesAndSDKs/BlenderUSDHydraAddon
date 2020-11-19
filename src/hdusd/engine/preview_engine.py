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
from ..export import depsgraph as dg

import numpy as np

from pxr import UsdImagingGL, UsdImagingLite

from ..utils import logging
log = logging.Log(tag='PreviewEngine')


class PreviewEngine(FinalEngine):
    """ Render engine for preview material, lights, environment """

    TYPE = 'PREVIEW'

    def render(self, scene):
        return

    def sync(self, depsgraph):

        def notify_callback(info):
            log(0.0, info)

        def test_break():
            return self.render_engine.test_break()

        scene = depsgraph.scene
        view_layer = depsgraph.view_layer
        settings_scene = bpy.context.scene
        self.is_gl_delegate = scene.hdusd.final.is_opengl
        self.render_layer_name = view_layer.name

        self.width = scene.render.resolution_x
        self.height = scene.render.resolution_y
        screen_ratio = self.width / self.height
        log(f"screen {self.width}x{self.height}, ratio {screen_ratio}")

        if not self.stage:
            self.stage = dg.sync(
                depsgraph,
                screen_ratio=screen_ratio,
                is_gl_delegate=self.is_gl_delegate,
                notify_callback=notify_callback,
                test_break=test_break,
                engine=self,
            )

        self.render_engine.bl_use_gpu_context = self.is_gl_delegate

        log(f"Sync finished")
