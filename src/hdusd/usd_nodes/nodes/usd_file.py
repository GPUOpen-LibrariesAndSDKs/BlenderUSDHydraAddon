# **********************************************************************
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
# ********************************************************************
import os
import re

import bpy
from pxr import Usd, UsdGeom, Sdf, Gf

from .base_node import USDNode
from . import log
from ...utils.usd import set_timesamples_for_stage

class UsdFileNode(USDNode):
    ''' read USD file '''
    bl_idname = 'usd.UsdFileNode'
    bl_label = "USD File"
    bl_icon = "FILE"
    bl_width_default = 250
    bl_width_min = 250

    input_names = ()
    use_hard_reset = True

    def update_data(self, context):
        self.reset(True)

    def set_end_frame(self, value):
        self['end_frame'] = self.start_frame if value < self.start_frame else value

    def get_end_frame(self):
        return self.get('end_frame', 0)

    def update_start_frame(self, context):
        if self.start_frame > self.end_frame:
            self.end_frame = self.start_frame

        self.update_data(context)

    def update_filename(self, context):
        if not self.filename:
            return None

        file_path = bpy.path.abspath(self.filename)
        if not os.path.isfile(file_path):
            return None

        input_stage = Usd.Stage.Open(file_path)

        self['start_frame'] = int(input_stage.GetMetadata('startTimeCode'))
        self['end_frame'] = int(input_stage.GetMetadata('endTimeCode'))

        self.update_data(context)

    filename: bpy.props.StringProperty(
        name="USD File",
        subtype='FILE_PATH',
        update=update_filename,
    )

    filter_path: bpy.props.StringProperty(
        name="Pattern",
        description="USD Path pattern. Use special characters means:\n"
                    "  * - any word or subword\n"
                    "  ** - several words separated by '/' or subword",
        default='/*',
        update=update_data
    )

    is_import_animation: bpy.props.BoolProperty(
        name="Import animation",
        description="Import animation",
        default=True,
        update=update_data
    )

    is_restrict_frames: bpy.props.BoolProperty(
        name="Set frames",
        description="Set frames to export",
        default=False,
        update=update_data
    )

    start_frame: bpy.props.IntProperty(
        name="Start frame",
        description="Start frame to export",
        default=0,
        update=update_start_frame
    )

    end_frame: bpy.props.IntProperty(
        name="End frame",
        description="End frame to export",
        default=0,
        set=set_end_frame, get=get_end_frame,
        update=update_data
    )

    def draw_buttons(self, context, layout):
        layout.prop(self, 'filename')
        layout.prop(self, 'filter_path')
        layout.prop(self, 'is_import_animation')

        if self.is_import_animation:
            layout.prop(self, 'is_restrict_frames')

        if self.is_import_animation and self.is_restrict_frames:
            row = layout.row(align=True)
            row.prop(self, 'start_frame')
            row.prop(self, 'end_frame')

    def compute(self, **kwargs):
        if not self.filename:
            return None

        file_path = bpy.path.abspath(self.filename)
        if not os.path.isfile(file_path):
            log.warn("Couldn't find USD file", self.filename, self)
            return None

        input_stage = Usd.Stage.Open(file_path)

        if self.filter_path == '/*':
            set_timesamples_for_stage(input_stage,
                                      is_use_animation=self.is_import_animation,
                                      is_restrict_frames=self.is_restrict_frames,
                                      start=self.start_frame,
                                      end=self.end_frame)

            self.cached_stage.insert(input_stage)
            return input_stage

        # creating search regex pattern and getting filtered rpims
        prog = re.compile(self.filter_path.replace('*', '#')        # temporary replacing '*' to '#'
                          .replace('/', '\/')       # for correct regex pattern
                          .replace('##', '[\w\/]*') # creation
                          .replace('#', '\w*'))

        def get_child_prims(prim):
            if not prim.IsPseudoRoot() and prog.fullmatch(str(prim.GetPath())):
                yield prim
                return

            for child in prim.GetAllChildren():
                yield from get_child_prims(child)

        prims = tuple(get_child_prims(input_stage.GetPseudoRoot()))
        if not prims:
            return None

        stage = self.cached_stage.create()
        stage.SetInterpolationType(Usd.InterpolationTypeHeld)
        UsdGeom.SetStageMetersPerUnit(stage, 1)
        UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)

        stage.SetMetadata('startTimeCode', input_stage.GetStartTimeCode())
        stage.SetMetadata('endTimeCode', input_stage.GetEndTimeCode())

        root_prim = stage.GetPseudoRoot()
        for i, prim in enumerate(prims, 1):
            override_prim = stage.OverridePrim(root_prim.GetPath().AppendChild(prim.GetName()))
            override_prim.GetReferences().AddReference(input_stage.GetRootLayer().realPath, prim.GetPath())

        set_timesamples_for_stage(stage,
                                  is_use_animation=self.is_import_animation,
                                  is_restrict_frames=self.is_restrict_frames,
                                  start=self.start_frame,
                                  end=self.end_frame)

        return stage
