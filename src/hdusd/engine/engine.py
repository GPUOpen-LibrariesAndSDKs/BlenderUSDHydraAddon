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
import weakref
import traceback

import bpy

from pxr import UsdGeom

from ..utils.stage_cache import CachedStage
from ..utils import depsgraph_objects
from ..export import sdf_path, object, world

from ..utils import logging
log = logging.Log(tag='engine')


class Engine:
    """ This is the basic Engine class """
    TYPE = None

    def __init__(self, render_engine):
        self.render_engine = weakref.proxy(render_engine)
        self.cached_stage = CachedStage()

    @property
    def stage(self):
        return self.cached_stage()

    def _export_depsgraph(self, stage, depsgraph: bpy.types.Depsgraph, **kwargs):
        log("sync", depsgraph)

        sync_callback = kwargs.get('sync_callback')
        test_break = kwargs.get('test_break')
        space_data = kwargs.get('space_data')
        use_scene_lights = kwargs.get('use_scene_lights', True)

        UsdGeom.SetStageMetersPerUnit(stage, 1)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)

        root_prim = stage.DefinePrim(f"/{sdf_path(depsgraph.scene.name)}")
        stage.SetDefaultPrim(root_prim)

        objects_prim = stage.DefinePrim(f"{root_prim.GetPath()}/objects")

        objects_len = len(depsgraph.objects)
        for i, obj in enumerate(depsgraph_objects(depsgraph, space_data, use_scene_lights)):
            if test_break and test_break():
                return None

            if sync_callback:
                sync_callback(f"Syncing object {i}/{objects_len}: {obj.name}")

            try:
                object.sync(objects_prim, obj, **kwargs)
            except Exception as e:
                log.error(e)

        world.sync(root_prim, depsgraph.scene.world, **kwargs)


from . import final_engine, viewport_engine, preview_engine


class HdUSDEngine(bpy.types.RenderEngine):
    """
    Main class of USD Hydra render engine for Blender
    """
    bl_idname = "HdUSD"
    bl_label = "USD Hydra"
    bl_use_preview = True
    bl_use_shading_nodes = True
    bl_use_shading_nodes_custom = False
    bl_use_gpu_context = False
    bl_info = "USD Hydra rendering plugin"

    engine: Engine = None

    def __del__(self):
        log('__del__', self.as_pointer())

    def update(self, data, depsgraph):
        """ Called for final render """
        log('update', self.as_pointer())

        try:
            if self.is_preview:
                engine_cls = preview_engine.PreviewEngine

            else:
                engine_cls = final_engine.FinalEngine

            self.engine = engine_cls(self)
            self.engine.sync(depsgraph)

        except Exception as e:
            log.error(e, 'EXCEPTION:', traceback.format_exc())
            self.error_set(f"ERROR | {e}. Please see log for more details.")

    def render(self, depsgraph):
        """ Called with for final render """
        log("render", self.as_pointer())
        try:
            self.engine.render(depsgraph)

        except Exception as e:
            log.error(e, 'EXCEPTION:', traceback.format_exc())
            self.error_set(f"ERROR | {e}. Please see log for more details.")

    # viewport render
    def view_update(self, context, depsgraph):
        """ Called when data is updated for viewport """
        log('view_update', self.as_pointer())

        try:
            if self.engine:
                self.engine.sync_update(context, depsgraph)
                return

            self.engine = viewport_engine.ViewportEngine(self)
            self.engine.sync(context, depsgraph)

        except Exception as e:
            log.error(e, 'EXCEPTION:', traceback.format_exc())

    def view_draw(self, context, depsgraph):
        """ called when viewport is to be drawn """
        log('view_draw', self.as_pointer())

        try:
            self.engine.draw(context)

        except Exception as e:
            log.error(e, 'EXCEPTION:', traceback.format_exc())
