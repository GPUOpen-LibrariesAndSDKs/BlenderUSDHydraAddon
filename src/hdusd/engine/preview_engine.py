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
import threading
import numpy as np

from pxr import UsdGeom, UsdAppUtils, Tf
from pxr import UsdImagingLite

from .engine import Engine
from ..utils.stage_cache import CachedStage
from ..export import object, world

from ..utils import logging
log = logging.Log('preview_engine')


class PreviewEngine(Engine):
    """ Render engine for preview material, lights, environment """

    TYPE = 'PREVIEW'
    SAMPLES_NUMBER = 50
    RENDERER_LIFETIME = 60.0    # 1 minute in seconds

    renderer: UsdImagingLite.Engine = None
    cached_stage: CachedStage = None
    timer: threading.Timer = None    # timer to remove rpr_context

    @classmethod
    def _remove_renderer(cls):
        log("Removing renderer")
        cls.renderer = None
        cls.cached_stage = None
        cls.timer = None

    def __init__(self, render_engine):
        super().__init__(render_engine)

        cls = self.__class__

        if cls.timer:
            cls.timer.cancel()

        if not cls.renderer:
            log("Creating renderer")
            cls.renderer = UsdImagingLite.Engine()
            cls.renderer.SetRendererPlugin('HdRprPlugin')
            cls.cached_stage = CachedStage()
            stage = cls.cached_stage.create()
            UsdGeom.SetStageMetersPerUnit(stage, 1)
            UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)

        self.renderer = cls.renderer
        self.cached_stage = cls.cached_stage
        self.is_synced = False

    def __del__(self):
        self.renderer.StopRenderer()

        cls = self.__class__
        cls.timer = threading.Timer(cls.RENDERER_LIFETIME, cls._remove_renderer)
        cls.timer.start()

    def sync(self, depsgraph):
        self.is_synced = False

        stage = self.stage

        for prim in stage.GetPseudoRoot().GetAllChildren():
            stage.RemovePrim(prim.GetPath())

        root_prim = stage.GetPseudoRoot()

        for obj_data in object.ObjectData.depsgraph_objects(depsgraph, use_scene_cameras=False):
            if self.render_engine.test_break():
                return None

            object.sync(root_prim, obj_data, is_preview_render=True)

        world.sync(root_prim, depsgraph.scene.world)

        object.sync(stage.GetPseudoRoot(), object.ObjectData.from_object(depsgraph.scene.camera),
                    scene=depsgraph.scene)

        self.is_synced = True
        log(f"Sync finished")

    def render(self, depsgraph):
        if not self.is_synced:
            return

        scene = depsgraph.scene
        width, height = scene.render.resolution_x, scene.render.resolution_y

        # uses for creating a transparent background icon to follow blender UI style
        is_preview_icon = width == 32 and height == 32

        self.renderer.SetRendererSetting('rpr:maxSamples', self.SAMPLES_NUMBER)
        self.renderer.SetRendererSetting('rpr:core:renderQuality', 'Northstar')
        self.renderer.SetRendererSetting('rpr:alpha:enable', is_preview_icon)
        self.renderer.SetRendererSetting('rpr:adaptiveSampling:minSamples', 16)
        self.renderer.SetRendererSetting('rpr:adaptiveSampling:noiseTreshold', 0.05)

        self.renderer.ClearRendererAovs()
        self.renderer.SetRenderViewport((0, 0, width, height))
        self.renderer.SetRendererAov('color')

        # setting camera
        usd_camera = UsdAppUtils.GetCameraAtPath(self.stage, Tf.MakeValidIdentifier(scene.camera.data.name))

        gf_camera = usd_camera.GetCamera()
        self.renderer.SetCameraState(gf_camera)

        params = UsdImagingLite.RenderParams()
        image = np.zeros((width, height, 4), dtype=np.float32)

        def update_render_result():
            result = self.render_engine.begin_result(0, 0, width, height)
            render_passes = result.layers[0].passes
            render_passes.foreach_set('rect', image.flatten())
            self.render_engine.end_result(result)

        while True:
            if self.render_engine.test_break():
                break

            try:
                self.renderer.Render(self.stage.GetPseudoRoot(), params)

            except Exception as e:
                # known RenderMan issue https://github.com/PixarAnimationStudios/USD/issues/1415
                if isinstance(e, Tf.ErrorException) and "Failed to load plugin 'rmanOslParser'" in str(e):
                    pass  # we won't log error "GL error: invalid operation"
                else:
                    log.error(e)

            if self.renderer.IsConverged():
                break

            self.renderer.GetRendererAov('color', image.ctypes.data)
            update_render_result()

        self.renderer.GetRendererAov('color', image.ctypes.data)
        update_render_result()
