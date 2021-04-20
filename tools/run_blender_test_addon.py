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
import sys
import os
import subprocess
from pathlib import Path


def main(*blender_args):
    blender_exe = os.environ['BLENDER_EXE']
    os.environ['HDUSD_BLENDER_DEBUG'] = "1"

    # Running Blender
    start_script = Path(__file__).parent / "bl_scripts/start_test_addon.py"
    call_args = [blender_exe, *blender_args, '--python', str(start_script)]
    print("Running blender:", call_args)
    subprocess.check_call(call_args)


if __name__ == "__main__":
    main(*sys.argv[1:])
