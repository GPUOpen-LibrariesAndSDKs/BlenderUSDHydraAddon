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
from pathlib import Path

from build import rm_dir, check_call, OS


def main(bin_dir, clean, build_var, *args):
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
        # applying patch data/USD_deps.patch
        # fixes issues with building USD on python 3.10
        check_call('git', 'apply', str(repo_dir / "tools/data/USD_deps.patch"))

        # modifying pxr/usdImaging/CMakeLists.txt
        usd_imaging_lite_path = repo_dir / "deps/UsdImagingLite/pxr/usdImaging/usdImagingLite"

        usd_imaging_cmake = usd_dir / "pxr/usdImaging/CMakeLists.txt"
        print("Modifying:", usd_imaging_cmake)
        cmake_txt = usd_imaging_cmake.read_text()
        usd_imaging_cmake.write_text(cmake_txt + f"""
add_subdirectory("{usd_imaging_lite_path.absolute().as_posix()}" usdImagingLite)
        """)

        bin_usd_dir = bin_dir / "USD"
        build_args = [f'MATERIALX,-DMATERIALX_BUILD_PYTHON=ON -DMATERIALX_INSTALL_PYTHON=OFF '
                      f'-DMATERIALX_PYTHON_EXECUTABLE="{sys.executable}"']
        if build_var == 'relwithdebuginfo' and OS == 'Windows':
            # disabling optimization for debug purposes
            build_args.append(f'USD,-DCMAKE_CXX_FLAGS_RELWITHDEBINFO="/Od"')

        call_args = (sys.executable, str(usd_dir / "build_scripts/build_usd.py"),
                     '--verbose',
                     '--build', str(bin_usd_dir / "build"),
                     '--src', str(bin_usd_dir / "deps"),
                     '--materialx',
                     '--openvdb',
                     '--build-args', *build_args,
                     '--python',
                     '--force', "OpenSubDiv",
                     '--build-variant', build_var,
                     str(bin_usd_dir / "install"),
                     *args)

        try:
            check_call(*call_args)

        finally:
            print("Reverting USD repo")
            check_call('git', 'checkout', '--', '*')
            check_call('git', 'clean', '-f')

    finally:
        os.chdir(cur_dir)


if __name__ == "__main__":
    main(*sys.argv[1:])
