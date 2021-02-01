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
import argparse
import os
import subprocess
from pathlib import Path


bl_scripts_dir = Path(__file__).parent / "bl_scripts"
blender_exe = os.environ['BLENDER_EXE']


def run_blender(script, v):
    call_args = [blender_exe, '--background', '--python', str(script)]
    if v:
        print("Running:", call_args)
    subprocess.check_call(call_args)


def main():
    ap = argparse.ArgumentParser()

    # Add the arguments to the parser
    ap.add_argument("-i", required=False, action="store_true",
                    help="Install USD Hydra addon")
    ap.add_argument("-u", required=False, action="store_true",
                    help="Uninstall USD Hydra addon")
    ap.add_argument("-r", required=False, action="store_true",
                    help="Reinstall USD Hydra addon")
    ap.add_argument("-v", required=False, action="store_true",
                    help="Visualize running process")
    args = ap.parse_args()

    if args.u or args.r:
        run_blender(bl_scripts_dir / "disable_addon.py", args.v)
        run_blender(bl_scripts_dir / "uninstall_addon.py", args.v)

    if args.i or args.r:
        run_blender(bl_scripts_dir / "install_addon.py", args.v)


if __name__ == "__main__":
    main()
