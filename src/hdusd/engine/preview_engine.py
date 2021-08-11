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
import numpy as np

from pxr import UsdGeom, UsdAppUtils, Tf
from pxr import UsdImagingLite

from .engine import Engine
from ..export import object, world

from ..utils import logging
log = logging.Log(tag='preview_engine')


class PreviewEngine(Engine):
    """ Render engine for preview material, lights, environment """

    TYPE = 'PREVIEW'
    SAMPLES_NUMBER = 50

    def _set_scene_camera(self, renderer, scene):
        usd_camera = UsdAppUtils.GetCameraAtPath(self.stage, Tf.MakeValidIdentifier(scene.camera.data.name))
        gf_camera = usd_camera.GetCamera()
        renderer.SetCameraState(gf_camera.frustum.ComputeViewMatrix(),
                                gf_camera.frustum.ComputeProjectionMatrix())

    def sync(self, depsgraph):
        stage = self.cached_stage.create()

        UsdGeom.SetStageMetersPerUnit(stage, 1)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)

        root_prim = stage.GetPseudoRoot()

        for obj_data in object.ObjectData.depsgraph_objects(depsgraph, use_scene_cameras=False):
            if self.render_engine.test_break():
                return None

            object.sync(root_prim, obj_data)

        world.sync(root_prim, depsgraph.scene.world)

        object.sync(stage.GetPseudoRoot(), object.ObjectData.from_object(depsgraph.scene.camera),
                    scene=depsgraph.scene)

        log(f"Sync finished")

    def render(self, depsgraph):
        scene = depsgraph.scene
        width, height = scene.render.resolution_x, scene.render.resolution_y

        renderer = UsdImagingLite.Engine()
        renderer.SetRendererPlugin('HdRprPlugin')
        renderer.SetRendererSetting('maxSamples', self.SAMPLES_NUMBER)

        renderer.SetRenderViewport((0, 0, width, height))
        renderer.SetRendererAov('color')

        # setting camera
        usd_camera = UsdAppUtils.GetCameraAtPath(
            self.stage, Tf.MakeValidIdentifier(scene.camera.data.name))
        gf_camera = usd_camera.GetCamera()
        renderer.SetCameraState(gf_camera.frustum.ComputeViewMatrix(),
                                gf_camera.frustum.ComputeProjectionMatrix())

        params = UsdImagingLite.RenderParams()
        image = np.empty((width, height, 4), dtype=np.float32)

        def update_render_result():
            result = self.render_engine.begin_result(0, 0, width, height)
            render_passes = result.layers[0].passes
            render_passes.foreach_set('rect', image.flatten())
            self.render_engine.end_result(result)

        renderer.Render(self.stage.GetPseudoRoot(), params)

        while True:
            if self.render_engine.test_break():
                break

            if renderer.IsConverged():
                break

            renderer.GetRendererAov('color', image.ctypes.data)
            update_render_result()

        renderer.GetRendererAov('color', image.ctypes.data)
        update_render_result()

        # its important to clear data explicitly
        renderer = None
