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
import traceback

import bpy


bl_info = {
    "name": "USD Hydra",
    "author": "AMD",
    "version": (1, 0, 0),
    "blender": (2, 90, 1),
    "location": "Info header, render engine menu",
    "description": "USD Hydra rendering plugin for Blender",
    "warning": "",
    "tracker_url": "",
    "wiki_url": "",
    "category": "Render"
}
version_build = ""


from . import config
from .utils import logging


log = logging.Log(tag='init')
log("Loading USD Hydra addon {}".format(bl_info['version']))


from .engine import final_engine, viewport_engine, preview_engine
from . import (
    properties,
    ui,
    operators,
    usd_nodes,
)


class HdEngine(bpy.types.RenderEngine):
    """
    Main class of Radeon ProRender render engine for Blender v2.80+
    """
    bl_idname = "HdUSD"
    bl_label = "USD Hydra"
    bl_use_preview = True
    bl_use_shading_nodes = True
    bl_use_shading_nodes_custom = False
    bl_use_gpu_context = False
    bl_info = "USD Hydra rendering plugin"

    engine = None

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

    # view layer AOVs
    def update_render_passes(self, render_scene=None, render_layer=None):
        """
        Update 'Render Layers' compositor node with active render passes info.
        Called by Blender.
        """
        # aovs = properties.view_layer.RPR_ViewLayerProperites.aovs_info
        #
        # scene = render_scene if render_scene else bpy.context.scene
        # layer = render_layer if render_scene else bpy.context.view_layer
        #
        # for index, enabled in enumerate(layer.rpr.enable_aovs):
        #     if enabled:
        #         pass_channel = aovs[index]['channel']
        #         pass_name = aovs[index]['name']
        #         pass_channels_size = len(pass_channel)
        #
        #         # convert from channel to blender type
        #         blender_type = 'VALUE'
        #         if pass_channel in ('RGB', 'RGBA'):
        #             blender_type = 'COLOR'
        #         elif pass_channel in {'XYZ', 'UVA'}:
        #             blender_type = 'VECTOR'
        #
        #         self.register_pass(scene, layer,
        #                            pass_name, pass_channels_size, pass_channel, blender_type)


@bpy.app.handlers.persistent
def on_version_update(*args, **kwargs):
    """ On scene loading update old RPR data to current version """
    log("on_version_update")


@bpy.app.handlers.persistent
def on_save_pre(*args, **kwargs):
    """ Handler on saving a blend file (before) """
    log("on_save_pre")


@bpy.app.handlers.persistent
def on_load_pre(*args, **kwargs):
    """ Handler on loading a blend file (before) """
    log("on_load_pre")
    utils.clear_temp_dir()


def register():
    """ Register all addon classes in Blender """
    log("register")

    bpy.utils.register_class(HdEngine)
    properties.register()
    operators.register()
    ui.register()
    usd_nodes.register()

    bpy.app.handlers.save_pre.append(on_save_pre)
    bpy.app.handlers.load_pre.append(on_load_pre)
    bpy.app.handlers.version_update.append(on_version_update)

    from .properties.usd_tree import SetupNodeData
    from .ui.usd_tree import SetupListFromNodeData
    SetupNodeData()
    SetupListFromNodeData()


def unregister():
    """ Unregister all addon classes from Blender """
    log("unregister")

    bpy.app.handlers.version_update.remove(on_version_update)
    bpy.app.handlers.load_pre.remove(on_load_pre)
    bpy.app.handlers.save_pre.remove(on_save_pre)

    usd_nodes.unregister()
    ui.unregister()
    operators.unregister()
    properties.unregister()
    bpy.utils.unregister_class(HdEngine)
