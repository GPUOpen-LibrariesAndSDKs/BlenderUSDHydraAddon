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

from .final_engine import FinalEngine
from ..export import depsgraph as dg, sdf_path

from pxr import UsdAppUtils

from ..utils import logging
log = logging.Log(tag='PreviewEngine')


class PreviewEngine(FinalEngine):
    """ Render engine for preview material, lights, environment """

    TYPE = 'PREVIEW'
    SAMPLES_NUMBER = 50

    def _set_scene_camera(self, renderer, scene):
        usd_camera = UsdAppUtils.GetCameraAtPath(self.stage, sdf_path('Camera.002'))
        gf_camera = usd_camera.GetCamera()
        renderer.SetCameraState(gf_camera.frustum.ComputeViewMatrix(),
                                gf_camera.frustum.ComputeProjectionMatrix())

    def sync(self, depsgraph):

        def notify_callback(info):
            log(0.0, info)

        def test_break():
            return self.render_engine.test_break()

        scene = depsgraph.scene
        self.render_layer_name = depsgraph.view_layer.name

        self.is_gl_delegate = False  # TODO fix Preview in the HdStorm mode

        self.width = scene.render.resolution_x
        self.height = scene.render.resolution_y
        screen_ratio = self.width / self.height

        if not self.stage:
            self.stage = dg.sync(
                depsgraph,
                screen_ratio=screen_ratio,
                is_gl_delegate=self.is_gl_delegate,
                notify_callback=notify_callback,
                test_break=test_break,
                engine=self,
                is_preview_render=True,
            )

        self.render_engine.bl_use_gpu_context = self.is_gl_delegate

        log(f"Sync finished")
