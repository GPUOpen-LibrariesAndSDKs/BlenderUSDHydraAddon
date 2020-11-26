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

from ..utils import logging
log = logging.Log(tag='export.nodegraph')


def sync(nodetree, **kwargs):
    output_node = nodetree.get_output_node()
    if not output_node:
        log.warn(f"Unable to find any suitable Output node in the USD Nodegraph.")
        return None

    stage = output_node.cstage()
    if not stage:
        stage = output_node.final_compute('Input', **kwargs)

    return stage

