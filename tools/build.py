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
from pathlib import Path
import subprocess
import os
import argparse
import sys
import platform
import shutil


OS = platform.system()
repo_dir = Path(__file__).parent.parent.resolve()


def rm_dir(d: Path):
    if not d.is_dir():
        return

    print(f"Removing: {d}")
    shutil.rmtree(str(d))


def usd(bin_dir, jobs, clean):
    import build_usd
    args = []
    if jobs > 0:
        args += ['-j', str(jobs)]

    build_usd.main(bin_dir, clean, *args)


def _cmake(ch_dir, compiler, jobs, args):
    cur_dir = os.getcwd()
    os.chdir(str(ch_dir))

    build_args = ['-B', 'build', *args]
    if compiler:
        build_args += ['-G', compiler]

    compile_args = [
        '--build', 'build',
        '--config', 'Release',
        '--target', 'install'
    ]
    if jobs > 0:
        compile_args += ['--', '-j', str(jobs)]

    try:
        subprocess.check_call(['cmake', *build_args])
        subprocess.check_call(['cmake', *compile_args])

    finally:
        os.chdir(cur_dir)


def hdrpr(bin_dir, compiler, jobs, clean):
    hybrid_pro_dir = repo_dir / "deps/BaikalNext"
    hdrpr_dir = repo_dir / "deps/HdRPR"

    if clean:
        rm_dir(hdrpr_dir / "build")
        rm_dir(bin_dir / "HdRPR")

    _cmake(hdrpr_dir, compiler, jobs, [
        f'-Dpxr_DIR={bin_dir / "USD/install"}',
        f'-DCMAKE_INSTALL_PREFIX={bin_dir / "HdRPR/install"}',
        '-DRPR_BUILD_AS_HOUDINI_PLUGIN=FALSE',
        f'-DRPR_LOCATION={hybrid_pro_dir.as_posix()}',
        f'-DRPR_LOCATION_LIB={(hybrid_pro_dir / "lib").as_posix()}',
        f'-DRPR_BIN_LOCATION={(hybrid_pro_dir / "bin").as_posix()}',
        f'-DRPR_LOCATION_INCLUDE={(hybrid_pro_dir / "inc/Rpr").as_posix()}',
        f'-DRPR_TOOLS_LOCATION={(hdrpr_dir / "deps/RPR/RadeonProRender/rprTools").as_posix()}',
    ])


def materialx(bin_dir, compiler, jobs, clean):
    mx_dir = repo_dir / "deps/HdRPR/deps/MaterialX"

    if clean:
        rm_dir(mx_dir / "build")
        rm_dir(bin_dir / "MaterialX")

    _cmake(mx_dir, compiler, jobs, [
        f'-DCMAKE_INSTALL_PREFIX={bin_dir / "MaterialX/install"}',
        '-DMATERIALX_BUILD_PYTHON=ON',
        f'-DMATERIALX_PYTHON_EXECUTABLE={sys.executable}',
        '-DMATERIALX_INSTALL_PYTHON=OFF',
        '-DMATERIALX_BUILD_VIEWER=ON'
    ])


def libs(bin_dir):
    import create_libs
    create_libs.main(bin_dir)


def mx_classes():
    import generate_mx_classes
    generate_mx_classes.main()


def zip_addon():
    import create_zip_addon
    create_zip_addon.main()


def usd_debug_libs(bin_dir):
    import create_libs
    create_libs.copy_usd_debug_files(bin_dir)


def main():
    ap = argparse.ArgumentParser()

    # Add the arguments to the parser
    ap.add_argument("-all", required=False, action="store_true",
                    help="Build all")
    ap.add_argument("-usd", required=False, action="store_true",
                    help="Build USD")
    ap.add_argument("-hdrpr", required=False, action="store_true",
                    help="Build HdRPR")
    ap.add_argument("-mx", required=False, action="store_true",
                    help="Build MaterialX")
    ap.add_argument("-bin-dir", required=False, type=str, default="",
                    help="Path to binary directory")
    ap.add_argument("-libs", required=False, action="store_true",
                    help="Create libs dir")
    ap.add_argument("-mx-classes", required=False, action="store_true",
                    help="Generate MaterialX classes")
    ap.add_argument("-addon", required=False, action="store_true",
                    help="Create zip addon")
    ap.add_argument("-G", required=False, type=str, default="",
                    help="Compiler for HdRPR and MaterialX in cmake. "
                         'For example: -G "Visual Studio 15 2017 Win64"')
    ap.add_argument("-j", required=False, type=int, default=0,
                    help="Number of jobs run in parallel")
    ap.add_argument("-usd-debug-libs", required=False, action="store_true",
                    help="Copy RelWithDebInfo USD libs")
    ap.add_argument("-clean", required=False, action="store_true",
                    help="Clean build dirs before start USD, HdRPR or MaterialX build")

    args = ap.parse_args()

    if OS == 'Windows' and (args.all or args.hdrpr or args.mx) and not args.G:
        print('Please select compiler. For example: -G "Visual Studio 15 2017 Win64"')
        return

    bin_dir = Path(args.bin_dir).resolve() if args.bin_dir else (repo_dir / "bin")

    if args.all or args.usd:
        usd(bin_dir, args.j, args.clean)

    if args.all or args.hdrpr:
        hdrpr(bin_dir, args.G, args.j, args.clean)

    if args.all or args.mx:
        materialx(bin_dir, args.G, args.j, args.clean)

    if args.all or args.libs:
        libs(bin_dir)

    if args.all or args.mx_classes:
        mx_classes()

    if args.all or args.addon:
        zip_addon()

    if args.usd_debug_libs:
        usd_debug_libs(bin_dir)


if __name__ == "__main__":
    main()
