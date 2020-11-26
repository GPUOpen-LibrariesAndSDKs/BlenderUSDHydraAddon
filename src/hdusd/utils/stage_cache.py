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
import tempfile

import bpy
from pxr import Usd

from . import temp_pid_dir


_stage_cache = Usd.StageCache()


class StageCache:
    usd_id = -1
    is_owner = False

    def create_stage(self):
        self.clear_stage()
        stage = Usd.Stage.CreateNew(tempfile.mktemp(".usda", "tmp", temp_pid_dir()))
        self.usd_id = _stage_cache.Insert(stage).ToLongInt()
        self.is_owner = True
        return stage

    def insert_stage(self, stage):
        self.clear_stage()
        self.usd_id = _stage_cache.Insert(stage).ToLongInt()
        self.is_owner = True
        return stage

    @property
    def stage(self):
        if self.usd_id == -1:
            return None

        stage = _stage_cache.Find(Usd.StageCache.Id.FromLongInt(self.usd_id))
        if not stage:
            self.usd_id = -1
            self.is_owner = False

        return stage

    def assign_stage(self, stage):
        if self.usd_id == _stage_cache.GetId(stage).ToLongInt():
            return

        self.clear_stage()
        self.usd_id = _stage_cache.GetId(stage).ToLongInt()

    def clear_stage(self):
        if self.is_owner:
            _stage_cache.Erase(Usd.StageCache.Id.FromLongInt(self.usd_id))
            self.usd_id = -1
            self.is_owner = False
        else:
            self.usd_id = -1

    def __del__(self):
        self.clear_stage()


class StageCacheProp(StageCache):
    usd_id: bpy.props.IntProperty(default=-1)
    is_owner: bpy.props.BoolProperty(default=False)

    def __del__(self):
        pass
