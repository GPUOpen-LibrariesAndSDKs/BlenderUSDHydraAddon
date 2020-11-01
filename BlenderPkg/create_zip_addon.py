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
import zlib
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
        if f.is_dir():
            continue

        rel_path = f.relative_to(usd_plugin_dir)
        rel_path_parts = rel_path.parts
        if  rel_path_parts[0] in ("libs", "configdev.py", "hdusd.log") or \
                "__pycache__" in rel_path_parts or ".gitignore" in rel_path_parts:
            continue

        yield f, rel_path

    # copy legals and readmes
    for f in repo_dir.glob("*"):
        if f.name in ("LICENSE.txt", "README.md"):
            yield f, f.name

    # copy HDUSD libraries
    hdusd_libs_dir = Path(os.environ['HDUSD_LIBS_DIR'])
    for f in hdusd_libs_dir.glob("**/*"):
        if f.is_dir():
            continue

        rel_path = f.relative_to(hdusd_libs_dir.parent)
        if "__pycache__" in rel_path.parts:
            continue

        yield f, rel_path


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
    with zipfile.ZipFile(zip_addon, 'w', compression=zipfile.ZIP_DEFLATED,
                         compresslevel=zlib.Z_BEST_COMPRESSION) as myzip:
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
