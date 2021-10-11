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
import platform
import shutil
import subprocess
from pathlib import Path

from build import rm_dir


OS = platform.system()


def iterate_files(path, glob, *, ignore_parts=(), ignore_suffix=()):
    assert path.is_dir(), f"Directory {path} not exists"

    for f in path.glob(glob):
        if f.is_dir(): # or f.suffix in ignore_suffix or any(p in f.parts for p in ignore_parts):
            continue

        yield f


def iterate_copied_files(repo_dir, usd_dir):
    # USD, HdRPR libraries
    for f in iterate_files(usd_dir / "lib", "**/*",
                           ignore_parts=("__pycache__",),
                           ignore_suffix=(".cmake", ".pdb", ".lib", ".def")):
        # if "cmake" in f.name or "cmake" in f.relative_to(usd_dir / "lib").parts:
        #     continue
        yield f, Path("usd") / f.relative_to(usd_dir)

    if OS == 'Windows':
        yield usd_dir.parent / "build/openexr-2.3.0/OpenEXR/IlmImf/RelWithDebInfo/IlmImf-2_3.dll",\
              Path("usd") / "lib/IlmImf-2_3.dll"

    for f in iterate_files(usd_dir / "bin", "**/*",
                           ignore_suffix=('.pdb',)):
        yield f, Path("usd") / f.relative_to(usd_dir)

    for f in iterate_files(usd_dir / "plugin", "**/*",
                           ignore_suffix=(".lib",)):
        yield f, Path("usd") / f.relative_to(usd_dir)

    # MaterialX libraries
    for f in iterate_files(usd_dir / "python", "**/*",
                           ignore_suffix=(".lib",)):
        yield f, Path("usd") / f.relative_to(usd_dir)

    for f in iterate_files(usd_dir / "libraries", "**/*"):
        yield f, Path("usd") / f.relative_to(usd_dir)

    deps_mx_libs = repo_dir / "deps/mx_libs"
    for f in iterate_files(deps_mx_libs, "**/*"):
        yield f, Path("usd/libraries") / f.relative_to(deps_mx_libs)


def main(bin_dir):
    repo_dir = Path(__file__).parent.parent
    libs_dir = repo_dir / "libs"

    rm_dir(libs_dir)

    print(f"Copying libs to: {libs_dir}")

    for f, relative in iterate_copied_files(repo_dir, bin_dir / "USD/install"):
        print(f, '->', relative)

        f_copy = libs_dir / relative
        if not f_copy.parent.is_dir():
            f_copy.parent.mkdir(parents=True)

        shutil.copy(str(f), str(f_copy), follow_symlinks=False)

    if OS == 'Linux':
        print("Configuring rpath")
        patchelf_args = ['patchelf', '--set-rpath', "$ORIGIN/../../usd:$ORIGIN/../../hdrpr/lib",
                         str(libs_dir / 'plugins/usd/hdRpr.so')]
        print(patchelf_args)
        subprocess.check_call(patchelf_args)

        for glob in ("libIlm*.so", "libIex*.so", "libhio*.so", "libHalf*.so"):
            for f in iterate_files(libs_dir / "usd", glob):
                patchelf_args = ['patchelf', '--set-rpath', "$ORIGIN/.", str(f)]
                print(patchelf_args)
                subprocess.check_call(patchelf_args)

    # Clear usd/lib/python/rpr/RprUsd/__init__.py
    rpr_usd_init_py = libs_dir / "usd/lib/python/rpr/RprUsd/__init__.py"
    print(f"Clearing {rpr_usd_init_py}")
    rpr_usd_init_py.write_text("")

    print("Done.")


def copy_usd_debug_files(bin_dir):
    repo_dir = Path(__file__).parent.parent
    libs_dir = repo_dir / "libs"

    print(f"Copying USD debug build files to: {libs_dir / 'usd'}")

    for f in iterate_files(bin_dir / "USD/build/USD/pxr", "**/RelWithDebInfo/*"):
        if f.suffix not in ('.dll', '.pyd', '.pdb'):
            continue

        relative = Path("usd") / f.name
        print(f, '->', relative)

        f_copy = libs_dir / relative
        if not f_copy.parent.is_dir():
            f_copy.parent.mkdir(parents=True)

        shutil.copy(str(f), str(f_copy), follow_symlinks=False)

    print("Done.")


if __name__ == "__main__":
    main(Path(__file__).parent.parent / "bin")
