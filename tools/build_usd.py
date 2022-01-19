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
import shutil
from pathlib import Path

from build import rm_dir


def main(bin_dir, clean, *args):
    if len(args) == 1 and args[0] in ("--help", "-h"):
        print("""
Usage

  build_usd.py <bin-dir> [<args-for-USD/build_scripts/build_usd.py>...]
  
Specify arguments for build_scripts/build_usd.py script
in USD repository.
""")
        return

    repo_dir = Path(__file__).parent.parent
    usd_dir = repo_dir / "deps/USD"

    if clean:
        rm_dir(bin_dir / "USD")

    cur_dir = os.getcwd()
    os.chdir(str(usd_dir))

    try:
        # modifying pxr/usdImaging/CMakeLists.txt
        usd_imaging_lite_path = repo_dir / "deps/UsdImagingLite/pxr/usdImaging/usdImagingLite"

        usd_imaging_cmake = usd_dir / "pxr/usdImaging/CMakeLists.txt"
        print("Modifying:", usd_imaging_cmake)
        cmake_txt = usd_imaging_cmake.read_text()
        usd_imaging_cmake.write_text(cmake_txt + f"""
add_subdirectory("{usd_imaging_lite_path.absolute().as_posix()}" usdImagingLite)
        """)

        bin_usd_dir = bin_dir / "USD"
        call_args = (sys.executable, str(usd_dir / "build_scripts/build_usd.py"),
                     '--verbose',
                     '--build', str(bin_usd_dir / "build"),
                     '--src', str(bin_usd_dir / "deps"),
                     '--materialx',
                     '--openvdb',
                     '--build-args', f'MATERIALX,-DMATERIALX_BUILD_PYTHON=ON -DMATERIALX_INSTALL_PYTHON=OFF '
                                     f'-DMATERIALX_PYTHON_EXECUTABLE="{sys.executable}"',
                     '--python',
                     str(bin_usd_dir / "install"),
                     '--build-variant', 'release',
                     *args)

        try:
            print("Running:", call_args)
            subprocess.check_call(call_args)

        finally:
            print("Reverting USD repo")
            subprocess.check_call(('git', 'checkout', '--', '*'))
            subprocess.check_call(('git', 'clean', '-f'))

    finally:
        os.chdir(cur_dir)


if __name__ == "__main__":
    main(*sys.argv[1:])
