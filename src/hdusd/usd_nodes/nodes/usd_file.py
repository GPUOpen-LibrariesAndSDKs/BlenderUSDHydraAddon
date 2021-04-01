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

import bpy
from pxr import Usd

from .base_node import USDNode
from . import log


class UsdFileNode(USDNode):
    ''' read USD file '''
    bl_idname = 'usd.UsdFileNode'
    bl_label = "USD File"

    input_names = ()

    filename: bpy.props.StringProperty(name="USD File", subtype='FILE_PATH')

    def draw_buttons(self, context, layout):
        layout.prop(self, 'filename')

    def compute(self, **kwargs):
        if not self.filename:
            log.warn("USD file name not set, skipping node", self)
            return None

        file_path = bpy.path.abspath(self.filename)
        if not os.path.isfile(file_path):
            log.warn("Couldn't find USD file", self.filename, self)
            return None

        stage = Usd.Stage.Open(file_path)
        self.cached_stage.insert(stage)
        return stage
