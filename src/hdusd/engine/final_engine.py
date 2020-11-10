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
import time
import numpy as np

from pxr import Usd, UsdAppUtils, Glf
from pxr import UsdImagingGL, UsdImagingLite

import bgl

from .engine import Engine
from ..export import depsgraph as dg, nodegraph, sdf_path
from ..usd_nodes.node_tree import get_usd_nodetree
from ..utils import gl, time_str

from ..utils import logging
log = logging.Log(tag='RenderEngine')


class FinalEngine(Engine):
    """ Final render engine """

    TYPE = 'FINAL'

    def __init__(self, render_engine):
        super().__init__(render_engine)

        self.width = 0
        self.height = 0

        self.render_layer_name = None

        self.status_title = ""

        self.is_gl_delegate = False

    def notify_status(self, progress, info):
        """ Display export/render status """
        self.render_engine.update_progress(progress)
        self.render_engine.update_stats(self.status_title, info)
        log(f"Status [{progress:.2}]: {info}")

    def _render_gl(self, scene):
        CLEAR_COLOR = (0.0, 0.0, 0.0, 0.0)
        CLEAR_DEPTH = 1.0

        # creating draw_target
        draw_target = Glf.DrawTarget(self.width, self.height)
        draw_target.Bind()
        draw_target.AddAttachment("color", bgl.GL_RGBA, bgl.GL_FLOAT, bgl.GL_RGBA)
        draw_target.AddAttachment("depth", bgl.GL_DEPTH_COMPONENT, bgl.GL_FLOAT,
                                  bgl.GL_DEPTH_COMPONENT32F)

        # creating renderer
        renderer = UsdImagingGL.Engine()
        log("Hydra render:", scene.hdusd.final.delegate)
        renderer.SetRendererPlugin(scene.hdusd.final.delegate)

        # setting camera
        usd_camera = UsdAppUtils.GetCameraAtPath(
            self.stage, sdf_path(scene.camera.name))
        gf_camera = usd_camera.GetCamera()
        renderer.SetCameraState(gf_camera.frustum.ComputeViewMatrix(),
                                gf_camera.frustum.ComputeProjectionMatrix())

        renderer.SetRenderViewport((0, 0, self.width, self.height))
        renderer.SetRendererAov('color')

        bgl.glEnable(bgl.GL_DEPTH_TEST)
        bgl.glViewport(0, 0, self.width, self.height)
        bgl.glClearColor(*CLEAR_COLOR)
        bgl.glClearDepth(CLEAR_DEPTH)
        bgl.glClear(bgl.GL_COLOR_BUFFER_BIT | bgl.GL_DEPTH_BUFFER_BIT)

        root = self.stage.GetPseudoRoot()
        params = UsdImagingGL.RenderParams()
        params.renderResolution = (self.width, self.height)
        params.frame = Usd.TimeCode.Default()
        params.clearColor = CLEAR_COLOR

        try:
            renderer.Render(root, params)
        except Exception as e:
            log.error(e)

        self.update_render_result({
            'Combined': gl.get_framebuffer_data(self.width, self.height)
        })

        draw_target.Unbind()

        # its important to clear data explicitly
        draw_target = None
        renderer = None

    def _render(self, scene):
        # creating renderer
        renderer = UsdImagingLite.Engine()
        renderer.SetRendererPlugin(scene.hdusd.final.delegate)
        renderer.SetRenderViewport((0, 0, self.width, self.height))
        renderer.SetRendererAov('color')

        # setting camera
        usd_camera = UsdAppUtils.GetCameraAtPath(self.stage, sdf_path(scene.camera.name))
        gf_camera = usd_camera.GetCamera()
        renderer.SetCameraState(gf_camera.frustum.ComputeViewMatrix(),
                                gf_camera.frustum.ComputeProjectionMatrix())

        params = UsdImagingLite.RenderParams()
        params.samples = 200
        render_images = {
            'Combined': np.empty((self.width, self.height, 4), dtype=np.float32)
        }

        renderer.Render(self.stage.GetPseudoRoot(), params)

        time_begin = time.perf_counter()
        while True:
            if self.render_engine.test_break():
                break

            self.notify_status(0.0, f"Render Time: {time_str(time.perf_counter() - time_begin)}")

            if renderer.IsConverged():
                break

            renderer.GetRendererAov('color', render_images['Combined'].ctypes.data)
            self.update_render_result(render_images)

        renderer.GetRendererAov('color', render_images['Combined'].ctypes.data)
        self.update_render_result(render_images)

        renderer = None

    def render(self, depsgraph):
        if not self.stage:
            return

        scene = depsgraph.scene
        log(f"Start render [{self.width}, {self.height}]. "
            f"Hydra delegate: {scene.hdusd.final.delegate}")
        if self.render_engine.bl_use_gpu_context:
            self._render_gl(scene)
        else:
            self._render(scene)

        self.notify_status(1.0, "Finish render")

    def sync(self, depsgraph):
        scene = depsgraph.scene
        view_layer = depsgraph.view_layer
        self.is_gl_delegate = scene.hdusd.final.is_opengl
        self.render_layer_name = view_layer.name
        self.status_title = f"{scene.name}: {self.render_layer_name}"
        self.notify_status(0.0, "Start syncing")

        # Preparations for syncing
        time_begin = time.perf_counter()

        border = ((0, 0), (1, 1)) if not scene.render.use_border else \
            ((scene.render.border_min_x, scene.render.border_min_y),
             (scene.render.border_max_x - scene.render.border_min_x,
              scene.render.border_max_y - scene.render.border_min_y))

        screen_width = int(scene.render.resolution_x * scene.render.resolution_percentage / 100)
        screen_height = int(scene.render.resolution_y * scene.render.resolution_percentage / 100)

        self.width = int(screen_width * border[1][0])
        self.height = int(screen_height * border[1][1])
        screen_ratio = self.width / self.height

        def notify_callback(info):
            self.notify_status(0.0, info)

        def test_break():
            return self.render_engine.test_break()

        if scene.hdusd.final.is_usd_nodegraph:
            self.stage = nodegraph.sync(
                get_usd_nodetree(),
                depsgraph=depsgraph,
                screen_ratio=screen_ratio,
                is_gl_delegate=self.is_gl_delegate,
                notify_callback=notify_callback,
                test_break=test_break,
                engine=self,
            )
            if not self.stage:
                log.warn(f"Stage is empty, nothing to render. Check the USD nodegraph.")

        else:
            self.stage = dg.sync(
                depsgraph,
                screen_ratio=screen_ratio,
                is_gl_delegate=self.is_gl_delegate,
                notify_callback=notify_callback,
                test_break=test_break,
                engine=self,
            )

        if self.render_engine.test_break():
            log.warn("Syncing stopped by user termination")
            return

        # setting enabling/disabling gpu context in render() method
        self.render_engine.bl_use_gpu_context = self.is_gl_delegate

        log.info("Scene synchronization time:", time_str(time.perf_counter() - time_begin))
        self.notify_status(0.0, "Start render")

    def update_render_result(self, render_images):
        result = self.render_engine.begin_result(0, 0, self.width, self.height,
                                                 layer=self.render_layer_name)
        render_passes = result.layers[0].passes

        images = []
        for p in render_passes:
            image = render_images.get(p.name)
            if image is None:
                image = np.zeros((self.width, self.height, p.channels), dtype=np.float32)

            if p.channels != image.shape[2]:
                image = image[:, :, 0:p.channels]

            images.append(image.flatten())

        # efficient way to copy all AOV images
        render_passes.foreach_set('rect', np.concatenate(images))
        self.render_engine.end_result(result)
