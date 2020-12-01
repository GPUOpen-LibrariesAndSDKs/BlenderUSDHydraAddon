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

from pxr import Usd

from . import temp_pid_dir


ID_NO_STAGE = -1

_stage_cache = Usd.StageCache()


class CachedStage:
    id = ID_NO_STAGE
    is_owner = False

    def create(self):
        self.clear()
        stage = Usd.Stage.CreateNew(tempfile.mktemp(".usda", "tmp", temp_pid_dir()))
        self.id = _stage_cache.Insert(stage).ToLongInt()
        self.is_owner = True
        return stage

    def insert(self, stage):
        self.clear()
        self.id = _stage_cache.Insert(stage).ToLongInt()
        self.is_owner = True
        return stage

    def assign(self, stage):
        if not stage:
            self.clear()
            return

        if self.id == _stage_cache.GetId(stage).ToLongInt():
            return

        self.clear()
        self.id = _stage_cache.GetId(stage).ToLongInt()

    def clear(self):
        if self.is_owner:
            _stage_cache.Erase(Usd.StageCache.Id.FromLongInt(self.id))
            self.is_owner = False

        self.id = ID_NO_STAGE

    def __call__(self):
        if self.id == ID_NO_STAGE:
            return None

        stage = _stage_cache.Find(Usd.StageCache.Id.FromLongInt(self.id))
        if not stage:
            self.id = ID_NO_STAGE
            self.is_owner = False

        return stage

    def __del__(self):
        self.clear()

    def __bool__(self):
        return self.id != ID_NO_STAGE
