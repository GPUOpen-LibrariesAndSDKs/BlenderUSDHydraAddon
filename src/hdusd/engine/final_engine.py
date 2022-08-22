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
import threading
import math

from pxr import Usd, UsdAppUtils, Glf, Tf, UsdGeom
from pxr import UsdImagingGL, UsdImagingLite
from concurrent import futures

import bpy
import bgl

from .engine import Engine
from ..utils import gl, time_str, get_temp_file
from ..utils import usd as usd_utils
from ..export import object, world

from ..utils import logging
log = logging.Log('final_engine')


CHUNK_COUNT = 500


class FinalEngine(Engine):
    """ Final render engine """

    TYPE = 'FINAL'

    def __init__(self, render_engine):
        super().__init__(render_engine)

        self.width = 0
        self.height = 0

        self.render_layer_name = None

        self.status_title = ""

    def notify_status(self, progress, info):
        """ Display export/render status """
        self.render_engine.update_progress(progress)
        self.render_engine.update_stats(self.status_title, info)
        log(f"Status [{progress:.2}]: {info}")

    def _render_gl(self, scene):
        CLEAR_DEPTH = 1.0

        # creating draw_target
        draw_target = Glf.DrawTarget(self.width, self.height)
        draw_target.Bind()
        draw_target.AddAttachment("color", bgl.GL_RGBA, bgl.GL_FLOAT, bgl.GL_RGBA)

        # creating renderer
        renderer = UsdImagingGL.Engine()
        if not self._sync_render_settings(renderer, scene):
            renderer = None
            return

        # setting camera
        gf_camera = self.get_gf_camera(scene)
        renderer.SetCameraState(gf_camera.frustum.ComputeViewMatrix(),
                                gf_camera.frustum.ComputeProjectionMatrix())

        renderer.SetRenderViewport((0, 0, self.width, self.height))
        renderer.SetRendererAov('color')

        root = self.stage.GetPseudoRoot()
        params = UsdImagingGL.RenderParams()
        params.renderResolution = (self.width, self.height)
        params.frame = Usd.TimeCode(scene.frame_current)

        if scene.hdusd.final.data_source:
            world_data = world.WorldData.init_from_stage(self.stage)
        else:
            world_data = world.WorldData.init_from_world(scene.world)

        params.clearColor = world_data.clear_color

        try:
            renderer.Render(root, params)

        except Exception as e:
            log.error(e)

        self.update_render_result({
            'Combined': gl.get_framebuffer_data(self.width, self.height)
        })

        draw_target.Unbind()

        # it's important to clear data explicitly
        draw_target = None
        renderer = None

    def _render(self, scene):
        # creating renderer
        renderer = UsdImagingLite.Engine()
        if not self._sync_render_settings(renderer, scene):
            renderer = None
            return

        renderer.SetRenderViewport((0, 0, self.width, self.height))
        renderer.SetRendererAov('color')

        # setting camera
        gf_camera = self.get_gf_camera(scene)
        renderer.SetCameraState(gf_camera)

        params = UsdImagingLite.RenderParams()
        params.frame = Usd.TimeCode(scene.frame_current)

        render_images = {
            'Combined': np.empty((self.width, self.height, 4), dtype=np.float32)
        }

        time_begin = time.perf_counter()
        while True:
            if self.render_engine.test_break():
                break

            try:
                renderer.Render(self.stage.GetPseudoRoot(), params)

            except Exception as e:
                # known RenderMan issue https://github.com/PixarAnimationStudios/USD/issues/1415
                if isinstance(e, Tf.ErrorException) and "Failed to load plugin 'rmanOslParser'" in str(e):
                    pass  # we won't log error "GL error: invalid operation"
                else:
                    log.error(e)

            percent_done = usd_utils.get_renderer_percent_done(renderer)
            self.notify_status(percent_done / 100,
                               f"Render Time: {time_str(time.perf_counter() - time_begin)} | "
                               f"Done: {int(percent_done)}%")

            if renderer.IsConverged():
                break

            renderer.GetRendererAov('color', render_images['Combined'].ctypes.data)
            self.update_render_result(render_images)

        renderer.GetRendererAov('color', render_images['Combined'].ctypes.data)
        self.update_render_result(render_images)

        # explicit renderer deletion
        renderer = None

    def get_gf_camera(self, scene):
        if scene.hdusd.final.nodetree_camera != '' and scene.hdusd.final.data_source:
            usd_camera = UsdAppUtils.GetCameraAtPath(self.stage, scene.hdusd.final.nodetree_camera)
        else:
            usd_camera = UsdAppUtils.GetCameraAtPath(self.stage, Tf.MakeValidIdentifier(scene.camera.data.name))

        return usd_camera.GetCamera(scene.frame_current)

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
        settings = scene.hdusd.final
        view_layer = depsgraph.view_layer

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

        self._sync(depsgraph)

        usd_utils.set_delegate_variant_stage(self.stage, settings.delegate_name)

        if self.render_engine.test_break():
            log.warn("Syncing stopped by user termination")
            return

        # setting enabling/disabling gpu context in render() method
        self.render_engine.bl_use_gpu_context = settings.is_gl_delegate

        log.info("Scene synchronization time:", time_str(time.perf_counter() - time_begin))
        self.notify_status(0.0, "Start render")

    def _sync(self, depsgraph):
        pass

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

    def _sync_render_settings(self, renderer, scene):
        settings = scene.hdusd.final

        try:
            renderer.SetRendererPlugin(settings.delegate)
        except Exception as e:
            # RenderMan is not available for final and viewport render at the same time
            if isinstance(e, Tf.ErrorException) and "Could not initialize riley API" in str(e):
                self.render_engine.error_set('Cannot start final render when viewport render is running')
            else:
                self.render_engine.error_set(str(e))
                log.error(e)

            return False

        if settings.delegate == 'HdRprPlugin':
            hdrpr = settings.hdrpr
            quality = hdrpr.quality
            denoise = hdrpr.denoise

            renderer.SetRendererSetting('rpr:alpha:enable', hdrpr.enable_alpha)

            renderer.SetRendererSetting('rpr:core:renderQuality', hdrpr.render_quality)
            renderer.SetRendererSetting('rpr:core:renderMode', hdrpr.render_mode)

            renderer.SetRendererSetting('rpr:ambientOcclusion:radius', hdrpr.ao_radius)

            renderer.SetRendererSetting('rpr:maxSamples', hdrpr.max_samples)
            renderer.SetRendererSetting('rpr:adaptiveSampling:minSamples', hdrpr.min_adaptive_samples)
            renderer.SetRendererSetting('rpr:adaptiveSampling:noiseTreshold', hdrpr.variance_threshold)

            renderer.SetRendererSetting('rpr:quality:rayDepth', quality.max_ray_depth)
            renderer.SetRendererSetting('rpr:quality:rayDepthDiffuse', quality.max_ray_depth_diffuse)
            renderer.SetRendererSetting('rpr:quality:rayDepthGlossy', quality.max_ray_depth_glossy)
            renderer.SetRendererSetting('rpr:quality:rayDepthRefraction', quality.max_ray_depth_refraction)
            renderer.SetRendererSetting('rpr:quality:rayDepthGlossyRefraction', quality.max_ray_depth_glossy_refraction)
            renderer.SetRendererSetting('rpr:quality:rayDepthShadow', quality.max_ray_depth_shadow)
            renderer.SetRendererSetting('rpr:quality:raycastEpsilon', quality.raycast_epsilon)
            renderer.SetRendererSetting('rpr:quality:radianceClamping', quality.radiance_clamping)

            renderer.SetRendererSetting('rpr:denoising:enable', denoise.enable)
            renderer.SetRendererSetting('rpr:denoising:minIter', denoise.min_iter)
            renderer.SetRendererSetting('rpr:denoising:iterStep', denoise.iter_step)

            if hdrpr.render_quality == 'Northstar':
                renderer.SetRendererSetting('rpr:quality:imageFilterRadius', hdrpr.quality.pixel_filter_width)

        if settings.delegate == 'HdPrmanLoaderRendererPlugin':
            hdprman = settings.hdprman
            renderer.SetRendererSetting('convergedSamplesPerPixel', hdprman.samples)
            renderer.SetRendererSetting('convergedVariance', hdprman.variance_threshold)
            renderer.SetRendererSetting('interactiveIntegratorTimeout', hdprman.timeout)

        return True


class FinalEngineScene(FinalEngine):
    def _sync(self, depsgraph):
        stage = self.cached_stage.create()

        UsdGeom.SetStageMetersPerUnit(stage, 1)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)

        root_prim = stage.GetPseudoRoot()

        objects_len = sum(1 for _ in object.ObjectData.depsgraph_objects(depsgraph, use_scene_cameras=False))

        objects_stage = Usd.Stage.CreateNew(str(get_temp_file(".usda")))
        object_root_prim = objects_stage.GetPseudoRoot()

        for i, obj_data in enumerate(object.ObjectData.depsgraph_objects_obj(depsgraph, use_scene_cameras=False)):
            if self.render_engine.test_break():
                return

            self.notify_status(0.0, f"Syncing object {i}/{objects_len}: {obj_data.object.name}")

            object.sync(object_root_prim, obj_data)

        for prim in objects_stage.GetPseudoRoot().GetAllChildren():
            override_prim = stage.OverridePrim(root_prim.GetPath().AppendChild(prim.GetName()))
            override_prim.GetReferences().AddReference(objects_stage.GetRootLayer().realPath, prim.GetPath())

        instance_len = sum(1 for _ in object.ObjectData.depsgraph_objects_inst(depsgraph, use_scene_cameras=False))
        chunks = math.ceil(instance_len / CHUNK_COUNT)
        chunks_data = {}

        for i in range(chunks):
            chunk_stage = Usd.Stage.CreateNew(str(get_temp_file(".usda")))
            chunk_prim = stage.OverridePrim(f'/chunk_{i}')
            chunks_data[i] = {'stage': chunk_stage, 'prim': chunk_prim}

        objects_processed = 0
        threadLock = threading.Lock()

        def sync_chunk(idx, stage, prim):
            nonlocal objects_processed

            xform = UsdGeom.Xform.Define(stage, stage.GetPseudoRoot().GetPath().AppendChild(f'chunk_{idx}'))
            obj_prim = xform.GetPrim()

            for i, obj_data in enumerate(object.ObjectData.depsgraph_objects_inst(depsgraph, use_scene_cameras=False)):
                if i >= (idx) * CHUNK_COUNT and i < (idx + 1) * CHUNK_COUNT:
                    with threadLock:
                        objects_processed += 1

                    self.notify_status(0.0, f"Syncing instances: {objects_processed} / {instance_len}")
                    object.sync(obj_prim, obj_data, objects_stage)

            stage.SetDefaultPrim(obj_prim)

        with futures.ThreadPoolExecutor() as executor:
            chunk_sync = []

            for idx in chunks_data:
                chunk_sync.append(executor.submit(sync_chunk, idx,
                                                  chunks_data[idx]['stage'],
                                                  chunks_data[idx]["prim"]))

            for idx, future in enumerate(futures.wait(chunk_sync)):
                if idx == 0:
                    for i in chunks_data:
                        chunk_prim = stage.GetPrimAtPath(chunks_data[i]["prim"].GetPath())
                        chunk_prim.GetReferences().AddReference(chunks_data[i]['stage'].GetRootLayer().realPath)
                pass

        if depsgraph.scene.world is not None:
            world.sync(root_prim, depsgraph.scene.world)

        object.sync(stage.GetPseudoRoot(), object.ObjectData.from_object(depsgraph.scene.camera),
                    scene=depsgraph.scene)


class FinalEngineNodetree(FinalEngine):
    def _sync(self, depsgraph):
        settings = depsgraph.scene.hdusd.final
        output_node = bpy.data.node_groups[settings.data_source].get_output_node()

        if output_node is None:
            log.warn("Syncing stopped due to invalid output_node", output_node)
            return

        stage = output_node.cached_stage()
        self.cached_stage.assign(stage)
