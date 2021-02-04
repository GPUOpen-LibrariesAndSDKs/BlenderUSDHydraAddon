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
import subprocess
from pathlib import Path


def main(*args):
    if not args:
        print("""
Usage

  build_usd.py <path-to-USD-repo> [<args-for-USD/build_scripts/build_usd.py>...]
  
Specify path to USD repository and arguments for build_scripts/build_usd.py script
in USD repository.
""")
        return

    usd_path = Path(args[0])
    usd_imaging_lite_path = Path(__file__).parent.parent / "src/extras/usdImagingLite"

    usd_imaging_cmake = usd_path / "pxr/usdImaging/CMakeLists.txt"
    print("Modifying:", usd_imaging_cmake)
    cmake_txt = usd_imaging_cmake.read_text()
    usd_imaging_cmake.write_text(cmake_txt + f"""
add_subdirectory("{usd_imaging_lite_path.absolute().as_posix()}" usdImagingLite)
""")

    call_args = (sys.executable, str(usd_path / "build_scripts/build_usd.py"), *args[1:])
    print("Running:", call_args)
    subprocess.run(call_args)

    print("Reverting:", usd_imaging_cmake)
    usd_imaging_cmake.write_text(cmake_txt)


if __name__ == "__main__":
    main(*sys.argv[1:])
