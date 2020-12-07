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


class WriteFileNode(USDNode):
    """Writes stream out to USD file"""
    bl_idname = 'usd.WriteFileNode'
    bl_label = "Write USD File"

    file_path: bpy.props.StringProperty(name="USD File", subtype='FILE_PATH')

    def draw_buttons(self, context, layout):
        layout.prop(self, 'file_path')

    def compute(self, **kwargs):
        stage = self.get_input_link('Input', **kwargs)

        if stage and self.file_path:
            file_path = bpy.path.abspath(self.file_path)
            stage.Export(file_path)

        return stage
