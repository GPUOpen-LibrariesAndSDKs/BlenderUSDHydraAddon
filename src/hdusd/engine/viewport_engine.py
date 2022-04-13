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
from dataclasses import dataclass
import textwrap
import weakref
import time

import bpy
import bgl
from bpy_extras import view3d_utils

from pxr import Usd, UsdGeom, Tf, Gf, Glf
from pxr import UsdImagingGL

from .engine import Engine
from ..export import camera, material, object, world
from ..utils import usd as usd_utils
from ..utils import time_str
from ..utils import logging
log = logging.Log('viewport_engine')


@dataclass(init=False, eq=True)
class ViewSettings:
    """
    Comparable dataclass which holds render settings for ViewportEngine:
    - camera viewport settings
    - render resolution
    - screen resolution
    - render border
    """

    camera_data: camera.CameraData
    screen_width: int
    screen_height: int
    border: tuple

    def __init__(self, context: bpy.types.Context):
        """Initializes settings from Blender's context"""
        self.camera_data = camera.CameraData.init_from_context(context)
        self.screen_width, self.screen_height = context.region.width, context.region.height

        scene = context.scene

        # getting render border
        x1, y1 = 0, 0
        x2, y2 = self.screen_width, self.screen_height
        if context.region_data.view_perspective == 'CAMERA':
            if scene.render.use_border:
                # getting border corners from camera view

                # getting screen camera points
                camera_obj = scene.camera
                camera_points = camera_obj.data.view_frame(scene=scene)
                screen_points = tuple(
                    view3d_utils.location_3d_to_region_2d(context.region,
                                                          context.space_data.region_3d,
                                                          camera_obj.matrix_world @ p)
                    for p in camera_points
                )

                # getting camera view region
                x1 = min(p[0] for p in screen_points)
                x2 = max(p[0] for p in screen_points)
                y1 = min(p[1] for p in screen_points)
                y2 = max(p[1] for p in screen_points)

                # adjusting region to border
                x, y = x1, y1
                dx, dy = x2 - x1, y2 - y1
                x1 = int(x + scene.render.border_min_x * dx)
                x2 = int(x + scene.render.border_max_x * dx)
                y1 = int(y + scene.render.border_min_y * dy)
                y2 = int(y + scene.render.border_max_y * dy)

                # adjusting to region screen resolution
                x1 = max(min(x1, self.screen_width), 0)
                x2 = max(min(x2, self.screen_width), 0)
                y1 = max(min(y1, self.screen_height), 0)
                y2 = max(min(y2, self.screen_height), 0)

        else:
            if context.space_data.use_render_border:
                # getting border corners from viewport camera

                x, y = x1, y1
                dx, dy = x2 - x1, y2 - y1
                x1 = int(x + context.space_data.render_border_min_x * dx)
                x2 = int(x + context.space_data.render_border_max_x * dx)
                y1 = int(y + context.space_data.render_border_min_y * dy)
                y2 = int(y + context.space_data.render_border_max_y * dy)

        # getting render resolution and render border
        self.border = (x1, y1), (x2 - x1, y2 - y1)

    @property
    def width(self):
        return self.border[1][0]

    @property
    def height(self):
        return self.border[1][1]

    def export_camera(self):
        """Exports camera settings with render border"""
        return self.camera_data.export_gf(
            ((self.border[0][0] / self.screen_width, self.border[0][1] / self.screen_height),
             (self.border[1][0] / self.screen_width, self.border[1][1] / self.screen_height)))


class ViewportEngine(Engine):
    """ Basic Viewport render engine """

    TYPE = 'VIEWPORT'

    # Set of references of created ViewportEngine engines.
    # Will be used for notifications from other parts
    _engine_refs = set()

    @classmethod
    def get_engines(cls):
        for engine_ref in cls._engine_refs:
            engine = engine_ref()
            if isinstance(engine, cls):
                yield engine

    @classmethod
    def tag_redraw(cls):
        for engine in cls.get_engines():
            engine.render_engine.tag_redraw()

    def __init__(self, rpr_engine):
        super().__init__(rpr_engine)

        self.view_settings = None
        self.renderer = None
        self.render_params = None

        self.is_synced = False

        self.space_data = None
        self.shading_data = None

        self.is_gl_delegate = False

        self.data_source = ""

        self.time_begin = time.perf_counter()

        # adding current engine to engine refs
        self._engine_refs.add(weakref.ref(self))

    def __del__(self):
        # explicit renderer deletion
        self.renderer = None

        # removing current engine from _engine_refs
        self._engine_refs.remove(weakref.ref(self))

    def get_settings(self, scene):
        return scene.hdusd.viewport

    def notify_status(self, info, status, redraw=True):
        """ Display export progress status """
        log(f"Status: {status} | {info}")
        wrap_info = textwrap.fill(info, 120)
        self.render_engine.update_stats(status, wrap_info)

        if redraw:
            self.render_engine.tag_redraw()

    def sync(self, context, depsgraph):
        log('Start sync')

        scene = depsgraph.scene
        settings = self.get_settings(scene)

        self.is_gl_delegate = settings.is_gl_delegate

        self.space_data = context.space_data
        self.shading_data = world.ShadingData(context, depsgraph.scene.world)

        self.render_params = UsdImagingGL.RenderParams()
        self.render_params.frame = Usd.TimeCode(scene.frame_current)

        self.renderer = UsdImagingGL.Engine()

        self._sync(context, depsgraph)

        usd_utils.set_delegate_variant_stage(self.stage, settings.delegate_name)

        self.is_synced = True
        log('Finish sync')

    def sync_update(self, context, depsgraph):
        """ sync just the updated things """

        if not self.is_synced:
            return

        settings = self.get_settings(depsgraph.scene)
        self.render_params.frame = Usd.TimeCode(depsgraph.scene.frame_current)

        if self.renderer.IsPauseRendererSupported():
            self.renderer.PauseRenderer()

        if self._check_restart_renderer(depsgraph.scene):
            self.renderer = None    # explicit renderer deletion
            self.renderer = UsdImagingGL.Engine()

        gl_delegate_changed = self.is_gl_delegate != settings.is_gl_delegate

        self._sync_update(context, depsgraph)

        if gl_delegate_changed:
            usd_utils.set_delegate_variant_stage(self.cached_stage(), settings.delegate_name)

        if self.renderer.IsPauseRendererSupported():
            self.renderer.ResumeRenderer()

        self.render_engine.tag_redraw()

    def _sync(self, context, depsgraph):
        self._sync_render_settings(depsgraph.scene)

    def _sync_update(self, context, depsgraph):
        scene = next((update.id for update in depsgraph.updates
                      if isinstance(update.id, bpy.types.Scene)), None)
        if not scene:
            return

        self._sync_render_settings(scene)

    def draw(self, context):
        log("Draw")

        if not self.is_synced:
            return

        stage = self.stage
        if not stage:
            return

        view_settings = ViewSettings(context)
        if view_settings.width * view_settings.height == 0:
            return

        gf_camera = view_settings.export_camera()
        self.renderer.SetCameraState(gf_camera.frustum.ComputeViewMatrix(),
                                     gf_camera.frustum.ComputeProjectionMatrix())
        self.renderer.SetRenderViewport((*view_settings.border[0], *view_settings.border[1]))
        self.renderer.SetRendererAov('color')
        self.render_params.renderResolution = (view_settings.width, view_settings.height)
        self.render_params.clipPlanes = [Gf.Vec4d(i) for i in gf_camera.clippingPlanes]

        if self.is_gl_delegate:
            l = Glf.SimpleLight()
            l.ambient = (0, 0, 0, 0)
            l.position = (*gf_camera.frustum.position, 1)

            if not self.shading_data.type == 'MATERIAL':
                l.isDomeLight = True
                
            mat = Glf.SimpleMaterial()

            self.renderer.SetLightingState((l,), mat, (0, 0, 0, 0))

        bgl.glClear(bgl.GL_COLOR_BUFFER_BIT | bgl.GL_DEPTH_BUFFER_BIT)

        self.render_engine.bind_display_space_shader(context.scene)

        if usd_utils.get_renderer_percent_done(self.renderer) == 0.0:
            self.time_begin = time.perf_counter()

        try:
            self.renderer.Render(stage.GetPseudoRoot(), self.render_params)

        except Exception as e:
            if isinstance(e, Tf.ErrorException) and ("GL error: invalid operation" in str(e)
                                                     # known RenderMan issue https://github.com/PixarAnimationStudios/USD/issues/1415
                                                     or "Failed to load plugin 'rmanOslParser'" in str(e)):
                pass    # we won't log error "GL error: invalid operation"
            else:
                log.error(e)

        self.render_engine.unbind_display_space_shader()

        # additional clear of GL depth buffer which provides blender to draw viewport grid
        bgl.glClear(bgl.GL_DEPTH_BUFFER_BIT)

        elapsed_time = time_str(time.perf_counter() - self.time_begin)
        if not self.renderer.IsConverged():
            self.notify_status(f"Time: {elapsed_time} | "
                               f"Done: {int(usd_utils.get_renderer_percent_done(self.renderer))}%",
                               "Render")
        else:
            self.notify_status(f"Time: {elapsed_time}", "Rendering Done", False)

    def _sync_render_settings(self, scene):
        settings = self.get_settings(scene)

        self.is_gl_delegate = settings.is_gl_delegate

        try:
            self.renderer.SetRendererPlugin(settings.delegate)

        # special case for python 3.10 - first enable of viewport rendering throws exception
        # GlfSimpleShadowArray::_FreeBindlessTextures(void)'
        # called from UsdImagingGLEngine::_DestroyHydraObjects()
        except Exception as e:
            if isinstance(e, Tf.ErrorException) and "GL error: invalid value" in str(e):
                pass  # we won't log error "GL error: invalid value"
            else:
                log.error(e)

        if settings.delegate == 'HdRprPlugin':
            hdrpr = settings.hdrpr
            quality = hdrpr.interactive_quality
            denoise = hdrpr.denoise

            self.renderer.SetRendererSetting('rpr:alpha:enable', False)

            # self.renderer.SetRendererSetting('renderDevice', hdrpr.device)
            self.renderer.SetRendererSetting('rpr:core:renderQuality', hdrpr.render_quality)
            self.renderer.SetRendererSetting('rpr:core:renderMode', hdrpr.render_mode)

            self.renderer.SetRendererSetting('rpr:ambientOcclusion:radius', hdrpr.ao_radius)

            self.renderer.SetRendererSetting('rpr:maxSamples', hdrpr.max_samples)
            self.renderer.SetRendererSetting('rpr:adaptiveSampling:minSamples', hdrpr.min_adaptive_samples)
            self.renderer.SetRendererSetting('rpr:adaptiveSampling:noiseTreshold', hdrpr.variance_threshold)

            self.renderer.SetRendererSetting('rpr:quality:interactive:rayDepth', quality.max_ray_depth)
            self.renderer.SetRendererSetting('rpr:quality:interactive:downscale:enable', quality.enable_downscale)
            self.renderer.SetRendererSetting('rpr:quality:interactive:downscale:resolution', quality.resolution_downscale)

            self.renderer.SetRendererSetting('rpr:denoising:enable', denoise.enable)
            self.renderer.SetRendererSetting('rpr:denoising:minIter', denoise.min_iter)
            self.renderer.SetRendererSetting('rpr:denoising:iterStep', denoise.iter_step)

    def _check_restart_renderer(self, scene):
        restart = False

        settings = self.get_settings(scene)
        if settings.delegate == 'HdRprPlugin':
            hdrpr = settings.hdrpr
            restart = self.renderer.GetRendererSetting('rpr:core:renderQuality') != hdrpr.render_quality \
                      or self.renderer.GetRendererSetting('rpr:core:renderMode') != hdrpr.render_mode

        # temporary solution due to "material preview red painting" issue
        # we need to restart renderer to remove red from material after switching from material preview
        if settings.delegate == "HdStormRendererPlugin" and self.shading_data.type == 'MATERIAL':
            restart = True

        return restart


class ViewportEngineScene(ViewportEngine):
    """Viewport engine for rendering Blender current scene"""

    @classmethod
    def material_update(cls, material):
        for engine in cls.get_engines():
            engine.update_material(material)

    def update_material(self, mat):
        stage = self.cached_stage()
        material.sync_update_all(stage.GetPseudoRoot(), mat)
        self.render_engine.tag_redraw()

    def _sync(self, context, depsgraph):
        super()._sync(context, depsgraph)

        stage = self.cached_stage.create()

        log("sync", depsgraph)

        UsdGeom.SetStageMetersPerUnit(stage, 1)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)

        root_prim = stage.GetPseudoRoot()

        for obj_data in object.ObjectData.depsgraph_objects(
                depsgraph,
                space_data=self.space_data, use_scene_cameras=False,
                use_scene_lights=self.shading_data.use_scene_lights):
            object.sync(root_prim, obj_data)

        world.sync(root_prim, depsgraph.scene.world, self.shading_data)
        self.render_params.clearColor = world.get_clear_color(root_prim)

    def _sync_update(self, context, depsgraph):
        super()._sync_update(context, depsgraph)

        root_prim = self.stage.GetPseudoRoot()

        shading_data = world.ShadingData(context, depsgraph.scene.world)
        update_world = self.shading_data != shading_data
        update_collection = self.shading_data.use_scene_lights != shading_data.use_scene_lights
        self.shading_data = shading_data

        for update in depsgraph.updates:
            log("sync_update", update.id, type(update.id))

            if isinstance(update.id, (bpy.types.Collection, bpy.types.Scene)):
                update_collection = True
                continue

            if isinstance(update.id, bpy.types.Object):
                obj = update.id
                if obj.type == 'CAMERA':
                    continue

                if obj.type == 'LIGHT' and not self.shading_data.use_scene_lights:
                    continue

                # We need to update collection in any case of editing object because Blender doesn't have "is_hide" property
                update_collection = True

                obj_data = object.ObjectData.from_object(obj)

                object.sync_update(root_prim, obj_data,
                                   update.is_updated_geometry,
                                   update.is_updated_transform,
                                   is_gl_delegate=self.is_gl_delegate)

                for inst_obj_data in object.ObjectData.depsgraph_objects_inst(depsgraph):

                    if obj_data.sdf_name == object.sdf_name(inst_obj_data.parent) \
                            or obj_data.sdf_name == object.sdf_name(inst_obj_data.object):

                        object.sync_update(root_prim, inst_obj_data, update.is_updated_geometry,
                                           update.is_updated_transform)

                continue

            if isinstance(update.id, bpy.types.World):
                update_world = True
                continue

        if update_collection:
            self._sync_objects_collection(depsgraph)

        if update_world:
            world.sync_update(root_prim, depsgraph.scene.world, self.shading_data)
            self.render_params.clearColor = world.get_clear_color(root_prim)

    def _sync_objects_collection(self, depsgraph):
        root_prim = self.stage.GetPseudoRoot()

        def dg_objects():
            yield from object.ObjectData.depsgraph_objects(depsgraph,
                space_data=self.space_data,
                use_scene_lights=self.shading_data.use_scene_lights,
                use_scene_cameras=False)

        depsgraph_keys = set(obj_data.sdf_name for obj_data in dg_objects())
        usd_object_keys = set(prim.GetName() for prim in root_prim.GetAllChildren()
                              if prim.GetName() != world.OBJ_PRIM_NAME)
        keys_to_remove = usd_object_keys - depsgraph_keys
        keys_to_add = depsgraph_keys - usd_object_keys

        if keys_to_remove:
            log("Object keys to remove", keys_to_remove)
            for key in keys_to_remove:
                self.stage.RemovePrim(root_prim.GetPath().AppendChild(key))

        if keys_to_add:
            log("Object keys to add", keys_to_add)
            for obj_data in dg_objects():
                if obj_data.sdf_name not in keys_to_add:
                    continue

                object.sync(root_prim, obj_data)


class ViewportEngineNodetree(ViewportEngine):
    """Viewport engine for rendering USD Node Tree"""

    @classmethod
    def nodetree_output_node_computed(cls, nodetree):
        for engine in cls.get_engines():
            if engine.data_source != nodetree.name:
                continue

            output_node = nodetree.get_output_node()
            engine.nodetree_stage_changed(output_node.cached_stage() if output_node else None)

    def _sync(self, context, depsgraph):
        super()._sync(context, depsgraph)

        self.data_source = self.get_settings(depsgraph.scene).data_source

        stage = self.cached_stage.create()
        UsdGeom.SetStageMetersPerUnit(stage, 1)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)

        nodetree = bpy.data.node_groups[self.data_source]
        output_node = nodetree.get_output_node()
        self.nodetree_stage_changed(output_node.cached_stage() if output_node else None)

        world_data = world.WorldData.init_from_stage(self.stage)
        self.render_params.clearColor = world_data.clear_color

    def nodetree_stage_changed(self, stage):
        engine_stage = self.stage
        root_prim = engine_stage.GetPseudoRoot()

        # removing all prims in engine_stage
        for prim in engine_stage.GetPseudoRoot().GetAllChildren():
            engine_stage.RemovePrim(prim.GetPath())

        if stage:
            # creating overrides from nodetree stage
            for prim in stage.GetPseudoRoot().GetAllChildren():
                override_prim = engine_stage.OverridePrim(
                    root_prim.GetPath().AppendChild(prim.GetName()))
                override_prim.GetReferences().AddReference(stage.GetRootLayer().realPath,
                                                           prim.GetPath())

        self.render_engine.tag_redraw()
