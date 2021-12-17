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

from build import rm_dir, copy


OS = platform.system()


def iterate_files(path, glob, *, ignore_parts=(), ignore_suffix=()):
    assert path.is_dir(), f"Directory {path} not exists"

    for f in path.glob(glob):
        if f.is_dir() or f.suffix in ignore_suffix or any(p in f.parts for p in ignore_parts):
            continue

        yield f


def main(bin_dir):
    repo_dir = Path(__file__).parent.parent
    libs_dir = repo_dir / "libs"

    rm_dir(libs_dir)

    print(f"Copying libs to: {libs_dir}")

    usd_dir = bin_dir / "USD/install"
    libs_dir.mkdir(parents=True)

    copy(usd_dir / "bin", libs_dir / "bin", ('*.pdb',))
    copy(usd_dir / "lib", libs_dir / "lib", ("*.pdb", "*.lib", "*.def", "cmake", "__pycache__"))
    copy(usd_dir / "plugin", libs_dir / "plugin", ("*.pdb", "*.lib"))
    copy(usd_dir / "python", libs_dir / "python", ("*.lib", "build"))
    copy(usd_dir / "libraries", libs_dir / "libraries")
    copy(repo_dir / "deps/mx_libs/alglib", libs_dir / "libraries/alglib")

    if OS == 'Windows':
        copy(bin_dir / "USD/build/openexr-2.3.0/OpenEXR/IlmImf/Release/"
             "IlmImf-2_3.dll", libs_dir / "lib/IlmImf-2_3.dll")

    if OS == 'Linux':
        print("Configuring rpath")
        patchelf_args = ['patchelf', '--remove-rpath', str(libs_dir / 'plugin/usd/hdRpr.so')]
        print(patchelf_args)
        subprocess.check_call(patchelf_args)

        patchelf_args = ['patchelf', '--force-rpath', '--set-rpath', "$ORIGIN/../../lib",
                         str(libs_dir / 'plugin/usd/hdRpr.so')]
        print(patchelf_args)
        subprocess.check_call(patchelf_args)
        for glob in ("libIlm*.so", "libIex*.so", "libhio*.so", "libHalf*.so"):
            for f in iterate_files(libs_dir / "lib", glob):
                patchelf_args = ['patchelf', '--set-rpath', "$ORIGIN/.", str(f)]
                print(patchelf_args)
                subprocess.check_call(patchelf_args)

    # Clear lib/python/rpr/RprUsd/__init__.py
    rpr_usd_init_py = libs_dir / "lib/python/rpr/RprUsd/__init__.py"
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
