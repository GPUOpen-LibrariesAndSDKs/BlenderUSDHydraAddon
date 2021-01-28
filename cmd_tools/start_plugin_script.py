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

#script to load addon from within blender text editor

import faulthandler
from pathlib import Path
import sys

import bpy

sys.path.append(str((Path(__file__).parent.parent / 'src').resolve()))

faulthandler.enable()

import hdusd

hdusd.register()
bpy.context.scene.render.engine = 'HdUSD'
