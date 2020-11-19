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
from ..export import depsgraph as dg, sdf_path, camera

import numpy as np

from pxr import UsdAppUtils
from pxr import UsdImagingGL, UsdImagingLite

from ..utils import logging
log = logging.Log(tag='PreviewEngine')


class PreviewEngine(FinalEngine):
    """ Render engine for preview material, lights, environment """

    TYPE = 'PREVIEW'
    NUMBER_SAMPLES = 5

    def _render(self, scene):
        # creating renderer
        renderer = UsdImagingLite.Engine()
        renderer.SetRendererPlugin(scene.hdusd.final.delegate)
        renderer.SetRenderViewport((0, 0, self.width, self.height))
        renderer.SetRendererAov('color')

        # get Preview camera
        try:
            usd_camera = UsdAppUtils.GetCameraAtPath(self.stage, sdf_path('Camera.002'))
        except Exception as e:
            log.warn(f"Unable to get Preview camera:\n{str(e)}")
            return
        gf_camera = usd_camera.GetCamera()
        renderer.SetCameraState(gf_camera.frustum.ComputeViewMatrix(),
                                gf_camera.frustum.ComputeProjectionMatrix())

        # setup render params
        params = UsdImagingLite.RenderParams()
        params.samples = self.NUMBER_SAMPLES
        render_images = {
            'Combined': np.empty((self.width, self.height, 4), dtype=np.float32)
        }

        renderer.Render(self.stage.GetPseudoRoot(), params)

        log(f"_render()")

        while True:
            if self.render_engine.test_break():
                break

            if renderer.IsConverged():
                break

            renderer.GetRendererAov('color', render_images['Combined'].ctypes.data)
            self.update_render_result(render_images)

        renderer.GetRendererAov('color', render_images['Combined'].ctypes.data)
        self.update_render_result(render_images)

        log(f"_render finished")

        renderer = None

    def render(self, depsgraph):
        if not self.stage:
            return

        scene = depsgraph.scene
        log(f"Start render [{self.width}, {self.height}]. "
            f"Hydra delegate: {scene.hdusd.final.delegate}")

        self._render(scene)

    def sync(self, depsgraph):

        def notify_callback(info):
            log(0.0, info)

        def test_break():
            return self.render_engine.test_break()

        scene = depsgraph.scene
        self.render_layer_name = depsgraph.view_layer.name
        settings_scene = bpy.context.scene

        self.is_gl_delegate = scene.hdusd.final.is_opengl

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
