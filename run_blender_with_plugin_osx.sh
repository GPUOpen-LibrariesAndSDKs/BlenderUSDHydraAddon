#!/bin/bash

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

echo BLENDER_EXE "${BLENDER_EXE}"

DEBUGGER_EXE="$1"

if [ -x "${BLENDER_EXE}" ]; then
	python3 cmd_tools/run_blender.py "$BLENDER_EXE" cmd_tools/test_plugin.py "$DEBUGGER_EXE"

	exit

else

	echo "Could not find blender application"

fi

