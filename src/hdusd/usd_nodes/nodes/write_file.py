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
import bpy

from .base_node import USDNode
from ...utils.usd import set_timesamples_for_stage


class WriteFileNode(USDNode):
    """Writes stream out to USD file"""
    bl_idname = 'usd.WriteFileNode'
    bl_label = "Write USD File"
    bl_icon = "FILE_TICK"

    def set_frame_end(self, value):
        self['frame_end'] = self.frame_start if value < self.frame_start else value

    def get_frame_end(self):
        return self.get('frame_end', 0)

    def update_frame_start(self, context):
        if self.frame_start > self.frame_end:
            self.frame_end = self.frame_start

    file_path: bpy.props.StringProperty(name="USD File", subtype='FILE_PATH')

    is_export_animation: bpy.props.BoolProperty(
        name="Export animation",
        description="Export animation",
        default=True,
    )
    is_restrict_frames: bpy.props.BoolProperty(
        name="Set frames",
        description="Set frames to export",
        default=False,
    )
    frame_start: bpy.props.IntProperty(
        name="Start frame",
        description="Start frame to export",
        default=0,
        update=update_frame_start
    )
    frame_end: bpy.props.IntProperty(
        name="End frame",
        description="End frame to export",
        default=0,
        set=set_frame_end, get=get_frame_end
    )

    def draw_buttons(self, context, layout):
        layout.prop(self, 'file_path')
        layout.prop(self, 'is_export_animation')

        if self.is_export_animation:
            layout.prop(self, 'is_restrict_frames')

        if self.is_export_animation and self.is_restrict_frames:
            row = layout.row(align=True)
            row.prop(self, 'frame_start')
            row.prop(self, 'frame_end')

    def compute(self, **kwargs):
        input_stage = self.get_input_link('Input', **kwargs)

        if not input_stage:
            return None

        if not self.file_path:
            return input_stage

        stage = self.cached_stage.create()

        root_layer = stage.GetRootLayer()
        root_layer.TransferContent(input_stage.GetRootLayer())

        file_path = bpy.path.abspath(self.file_path)

        set_timesamples_for_stage(stage,
                                  is_use_animation=self.is_export_animation,
                                  is_restrict_frames=self.is_restrict_frames,
                                  start=self.frame_start,
                                  end=self.frame_end)

        stage.Export(file_path)

        return stage
