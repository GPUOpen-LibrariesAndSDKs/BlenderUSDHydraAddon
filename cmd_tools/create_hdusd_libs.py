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
import os
import shutil
from pathlib import Path
import argparse


def enumerate_libs(usd_dir, hdrpr_dir, mx_dir):
    # USD libraries
    for f in (usd_dir / "lib").glob("**/*"):
        if f.is_dir():
            continue
        if "__pycache__" in f.parts:
            continue
        if "cmake" in f.name or "cmake" in f.relative_to(usd_dir / "lib").parts:
            continue
        if f.suffix in (".cmake", ".pdb", ".lib", ".def"):
            continue

        yield f, Path("usd") / f.relative_to(usd_dir / "lib")

    for f in (usd_dir / "bin").glob("*.dll"):
        yield f, Path("usd") / f.relative_to(usd_dir / "bin")

    # copy RPR Hydra delegate libraries
    for f in (hdrpr_dir / "lib").glob("**/*"):
        if f.is_dir():
            continue
        if "python" in f.parts:
            continue
        if f.suffix == ".lib":
            continue

        yield f, Path("hdrpr") / f.relative_to(hdrpr_dir / "lib")

    # put all the plugins in the same folder so USD would load them all
    for f in (usd_dir / "plugin").glob("**/*"):
        if f.is_dir():
            continue

        yield f, Path("plugins") / f.relative_to(usd_dir / "./plugin")

    for f in (hdrpr_dir / "plugin").glob("**/*"):
        if f.is_dir():
            continue
        if "rprUsdviewMenu" in f.parts:
            continue
        if f.suffix == ".lib":
            continue

        yield f, Path("plugins") / f.relative_to(hdrpr_dir / "./plugin")

    # MaterialX libraries
    for f in (mx_dir / "python/MaterialX").glob("*"):
        if f.is_dir():
            continue
        if f.suffix in (".lib",):
            continue

        yield f, Path("materialx") / f.relative_to(mx_dir)


def main():
    ap = argparse.ArgumentParser()

    # Add the arguments to the parser
    ap.add_argument("-usd", required=True, metavar="",
                    help="USD dir")
    ap.add_argument("-hdrpr", required=True, metavar="",
                    help="HdRPR dir")
    ap.add_argument("-mx", required=True, metavar="",
                    help="MaterialX dir")
    ap.add_argument("-libs", required=False, metavar="",
                    help="Libs dir")
    args = ap.parse_args()

    if not args.libs:
        args.libs = os.environ['HDUSD_LIBS_DIR']

    libs_dir = Path(args.libs)
    if libs_dir.is_dir():
        shutil.rmtree(str(libs_dir))

    print("Copying libs to:", libs_dir)
    for f, relative in enumerate_libs(Path(args.usd), Path(args.hdrpr), Path(args.mx)):
        print(f, '->', relative)

        f_copy = libs_dir / relative
        if not f_copy.parent.is_dir():
            f_copy.parent.mkdir(parents=True)

        shutil.copy(str(f), str(f_copy))


if __name__ == "__main__":
    main()
