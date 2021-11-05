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

from .. import config
from ..utils.stage_cache import CachedStage

from ..utils import logging
log = logging.Log('engine')


class Engine:
    """ This is the basic Engine class """
    TYPE = None

    def __init__(self, render_engine):
        self.render_engine = weakref.proxy(render_engine)
        self.cached_stage = CachedStage()

    @property
    def stage(self):
        return self.cached_stage()


from . import final_engine, viewport_engine, preview_engine


class HdUSDEngine(bpy.types.RenderEngine):
    """
    Main class of USD Hydra render engine for Blender
    """
    bl_idname = "HdUSD"
    bl_label = "USD Hydra"
    bl_use_preview = config.engine_use_preview
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
                if depsgraph.scene.hdusd.final.data_source:
                    engine_cls = final_engine.FinalEngineNodetree
                else:
                    engine_cls = final_engine.FinalEngineScene

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
            data_source = depsgraph.scene.hdusd.viewport.data_source
            if self.engine and self.engine.data_source == data_source:
                self.engine.sync_update(context, depsgraph)
                return

            if data_source:
                self.engine = viewport_engine.ViewportEngineNodetree(self)
            else:
                self.engine = viewport_engine.ViewportEngineScene(self)

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
