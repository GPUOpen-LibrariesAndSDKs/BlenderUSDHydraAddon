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

import zipfile
import os
import platform
from pathlib import Path
import subprocess
import shutil
import re


OS = platform.system()

repo_dir = Path("..")


def enumerate_addon_data():
    # copy addon scripts
    usd_plugin_dir = repo_dir / 'src/hdusd'

    for f in usd_plugin_dir.glob("**/*"):
        if not f.is_file() or f.name in ("configdev.py", "rprblender.log"):
            continue

        if f.name.endswith('.py'):
            yield f, f.relative_to(usd_plugin_dir)

    # copy legals and readmes
    for f in repo_dir.glob("*"):
        if f.name in ("LICENSE.txt", "README.md"):
            yield f, f.name

    # copy USD libraries
    pixar_usd_dir = os.environ.get('USD_INSTALL_ROOT', '')
    if not pixar_usd_dir:
        raise EnvironmentError("Unable to locate USD build folder, use environment variable USD_INSTALL_ROOT")

    # copy USD libs and Python wrappers
    pixar_usd_dir = Path(pixar_usd_dir)

    for lib in (pixar_usd_dir / "./lib").glob("**/*"):
        if "__pycache__" in lib.parts:
            continue
        if "cmake" in lib.name or "cmake" in lib.relative_to(pixar_usd_dir / "./lib").parts:
            continue
        if lib.suffix in (".cmake", ".pdb", ".lib", ".def"):
            continue
        yield lib, Path("libs/usd") / lib.relative_to(pixar_usd_dir / "./lib")
    for lib in (pixar_usd_dir / "./bin").glob("*.dll"):
        yield lib, Path("libs/usd") / lib.relative_to(pixar_usd_dir / "./bin")

    # copy RPR Hydra delegate libraries
    hdrpr_plugin_dir = os.environ.get('USD_PLUGIN_ROOT', '')
    if not hdrpr_plugin_dir:
        raise EnvironmentError("Unable to locate hdRpr render delegate build folder, use environment variable USD_PLUGIN_ROOT")
    hdrpr_plugin_dir = Path(hdrpr_plugin_dir)

    for lib in (hdrpr_plugin_dir / "./lib").glob("**/*"):
        if "__pycache__" in lib.parts:
            continue
        if lib.suffix == ".lib":
            continue
        yield lib, Path("libs/hdrpr") / lib.relative_to(hdrpr_plugin_dir / "./lib")

    # put all the plugins in the same folder so USD would load them all
    for f in (pixar_usd_dir / "./plugin").glob("**/*"):
        if f.is_file():
            yield f, Path("libs/plugins") / f.relative_to(pixar_usd_dir / "./plugin")
    for lib in (hdrpr_plugin_dir / "./plugin").glob("**/*"):
        if lib.suffix == ".lib":
            continue
        yield lib, Path("libs/plugins") / lib.relative_to(hdrpr_plugin_dir / "./plugin")


def get_version():
    # getting buid version
    build_ver = subprocess.getoutput("git rev-parse --short HEAD")

    # getting plugin version
    text = (repo_dir / "src/hdusd/__init__.py").read_text()
    m = re.search(r'"version": \((\d+), (\d+), (\d+)\)', text)
    plugin_ver = m.group(1), m.group(2), m.group(3)

    return (*plugin_ver, build_ver)


def create_zip_addon(build_dir):
    """ Pack addon files to zip archive """
    ver = get_version()

    zip_addon = build_dir / f"hdusd-{ver[0]}.{ver[1]}.{ver[2]}-{ver[3]}-{OS.lower()}.zip"

    print(f"Compressing addon files to: {zip_addon}")
    with zipfile.ZipFile(zip_addon, 'w') as myzip:
        for src, package_path in enumerate_addon_data():
            print(f"adding {src} --> {package_path}")

            arcname = str(Path('hdusd') / package_path)

            if str(package_path) == "__init__.py":
                print(f"    set version_build={ver[3]}")
                text = src.read_text()
                text = text.replace('version_build = ""', f'version_build = "{ver[3]}"')
                myzip.writestr(arcname, text)
                continue

            myzip.write(str(src), arcname=arcname)

    return zip_addon


def main():
    build_dir = Path(".build")
    if build_dir.is_dir():
        shutil.rmtree(build_dir)
    build_dir.mkdir()

    zip_addon = create_zip_addon(build_dir)
    print(f"Addon was compressed to: {zip_addon}")


if __name__ == "__main__":
    main()
