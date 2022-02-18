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
import sys
from pathlib import Path
import subprocess
import os
import argparse
import platform
import shutil


OS = platform.system()
repo_dir = Path(__file__).parent.parent.resolve()


def rm_dir(d: Path):
    if not d.is_dir():
        return

    print(f"Removing: {d}")
    shutil.rmtree(str(d), ignore_errors=True)


def copy(src: Path, dest, ignore=()):
    print(f"Copying: {src} -> {dest}")
    if src.is_dir():
        shutil.copytree(str(src), str(dest), ignore=shutil.ignore_patterns(*ignore), symlinks=True)
    else:
        shutil.copy(str(src), str(dest), follow_symlinks=False)


def print_start(msg):
    print(f"""
-------------------------------------------------------------
{msg}
-------------------------------------------------------------""")


def usd(bin_dir, jobs, clean):
    print_start("Building USD")

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
    print_start("Building HdRPR")

    hdrpr_dir = repo_dir / "deps/HdRPR"
    usd_dir = bin_dir / "USD/install"

    if clean:
        rm_dir(hdrpr_dir / "build")

    os.environ['PXR_PLUGINPATH_NAME'] = str(usd_dir / "lib/usd")

    # If Python version from PATH differs from chosen version we need to add chosen version on top of PATH because
    # HdRPR doesn't get python version from argument
    if (python_dir := str(Path(sys.executable).parent)) not in os.environ['PATH']:
        os.environ['PATH'] = python_dir + ';' + os.environ['PATH']

    _cmake(hdrpr_dir, compiler, jobs, [
        f'-Dpxr_DIR={usd_dir}',
        f'-DCMAKE_INSTALL_PREFIX={bin_dir / "USD/install"}',
        '-DRPR_BUILD_AS_HOUDINI_PLUGIN=FALSE',
    ])


def libs(bin_dir):
    print_start("Copying binaries to libs")

    import create_libs
    create_libs.main(bin_dir)


def mx_classes():
    print_start("Generating code for MaterialX classes")

    import generate_mx_classes
    generate_mx_classes.main()


def zip_addon():
    print_start("Creating zip Addon")

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
    ap.add_argument("-bin-dir", required=False, type=str, default="",
                    help="Path to binary directory")
    ap.add_argument("-libs", required=False, action="store_true",
                    help="Create libs dir")
    ap.add_argument("-mx-classes", required=False, action="store_true",
                    help="Generate MaterialX classes")
    ap.add_argument("-addon", required=False, action="store_true",
                    help="Create zip addon")
    ap.add_argument("-G", required=False, type=str,
                    help="Compiler for HdRPR and MaterialX in cmake. "
                         'For example: -G "Visual Studio 15 2017 Win64"',
                    default="Visual Studio 15 2017 Win64" if OS == 'Windows' else "")
    ap.add_argument("-j", required=False, type=int, default=0,
                    help="Number of jobs run in parallel")
    ap.add_argument("-usd-debug-libs", required=False, action="store_true",
                    help="Copy RelWithDebInfo USD libs")
    ap.add_argument("-clean", required=False, action="store_true",
                    help="Clean build dirs before start USD, HdRPR or MaterialX build")

    args = ap.parse_args()

    if OS == 'Windows' and (args.all or args.hdrpr) and not args.G:
        print('Please select compiler. For example: -G "Visual Studio 15 2017 Win64"')
        return

    bin_dir = Path(args.bin_dir).resolve() if args.bin_dir else (repo_dir / "bin")
    bin_dir.mkdir(parents=True, exist_ok=True)

    if args.all or args.usd:
        usd(bin_dir, args.j, args.clean)

    if args.all or args.hdrpr:
        hdrpr(bin_dir, args.G, args.j, args.clean)

    if args.all or args.libs:
        libs(bin_dir)

    if args.all or args.mx_classes:
        mx_classes()

    if args.all or args.addon:
        zip_addon()

    if args.usd_debug_libs:
        usd_debug_libs(bin_dir)

    print_start("Finished")


if __name__ == "__main__":
    main()
