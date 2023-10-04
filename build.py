# **********************************************************************
# Copyright 2023 Advanced Micro Devices, Inc
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
import argparse
import platform
import shutil
import zipfile
import zlib
import os

OS = platform.system()
POSTFIX = ""
EXT = ".exe" if OS == 'Windows' else ""
LIBEXT = ".lib" if OS == 'Windows' else ".dylib" if OS == 'Darwin' else ".so"
LIBPREFIX = "" if OS == 'Windows' else "lib"

repo_dir = Path(__file__).parent.resolve()
deps_dir = repo_dir / "deps"
diff_dir = repo_dir / "patches"


def rm_dir(d: Path):
    if not d.is_dir():
        return

    print(f"Removing: {d}")
    shutil.rmtree(str(d), ignore_errors=True)


def ch_dir(d: [Path, str]):
    print(f"Chdir: {d}")
    os.chdir(str(d))


def check_call(*args):
    args_str = " ".join((f'"{arg}"' if ' ' in arg else arg) for arg in (arg.replace('"', r'\"') for arg in args))
    print(f"Running: {args_str}")
    subprocess.check_call(args)


def copy(src: Path, dest, ignore=()):
    print(f"Copying: {src} -> {dest}")
    if src.is_dir():
        shutil.copytree(str(src), str(dest), ignore=shutil.ignore_patterns(*ignore), symlinks=True)
    else:
        shutil.copy(str(src), str(dest), follow_symlinks=False)


def install_requirements(py_executable):
    with open("requirements.txt", "r") as file:
        required_modules = file.readlines()

    installed_modules = []
    for m in required_modules:
        try:
            check_call(py_executable, '-c', f'import {m}')

        except subprocess.CalledProcessError as e:
            check_call(py_executable, "-m", "pip", "install", f"{m}", "--user")
            installed_modules.append(m)

        except Exception as e:
            raise e

    return installed_modules


def uninstall_requirements(py_executable, installed_modules):
    for m in installed_modules:
        try:
            check_call(py_executable, "-m", "pip", "uninstall", f"{m}", "-y")
        except Exception as e:
            print("Error:", e)


def print_start(msg):
    print(f"""
-------------------------------------------------------------
{msg}
-------------------------------------------------------------""")


def _cmake(src_dir, bin_dir, compiler, jobs, build_var, clean, args):
    if clean:
        rm_dir(bin_dir)

    build_dir = bin_dir / "build"

    build_args = ['-B', str(build_dir),
                  '-S', str(src_dir),
                  '--install-prefix', (bin_dir / "install").as_posix(),
                  *args]
    if compiler:
        build_args += ['-G', compiler]

    if build_var == 'relwithdebuginfo' and OS == 'Windows':
        # disabling optimization for debug purposes
        build_args.append(f'-DCMAKE_CXX_FLAGS_RELWITHDEBINFO=/Od')

    build_name = {'release': 'Release',
                  'debug': 'Debug',
                  'relwithdebuginfo': 'RelWithDebInfo'}[build_var]

    compile_args = [
        '--build', str(build_dir),
        '--config', build_name,
        '--target', 'install'
    ]
    if jobs > 0:
        compile_args += ['--', '-j', str(jobs)]

    check_call('cmake', *build_args)
    check_call('cmake', *compile_args)


def materialx(bl_libs_dir, bin_dir, compiler, jobs, clean, build_var):
    libdir = bl_libs_dir.as_posix()
    py_exe = f"{libdir}/python/310/bin/python.exe" if OS == 'Windows' else\
             f"{libdir}/python/bin/python3.10"

    _cmake(deps_dir / "MaterialX", bin_dir / "materialx", compiler, jobs, build_var, clean, [
        '-DMATERIALX_BUILD_PYTHON=ON',
        '-DMATERIALX_BUILD_RENDER=ON',
        '-DMATERIALX_BUILD_VIEWER=ON',
        '-DMATERIALX_INSTALL_PYTHON=OFF',
        f'-DMATERIALX_PYTHON_EXECUTABLE={py_exe}',
        f'-DMATERIALX_PYTHON_VERSION=3.10',
        '-DMATERIALX_BUILD_SHARED_LIBS=ON',
        '-DMATERIALX_BUILD_TESTS=OFF',
        '-DCMAKE_DEBUG_POSTFIX=_d',
        f'-Dpybind11_ROOT=',
        f'-DPython_EXECUTABLE={py_exe}',
    ])


def usd(bl_libs_dir, bin_dir, compiler, jobs, clean, build_var, git_apply):
    print_start("Building USD")

    usd_dir = deps_dir / "USD"
    libdir = bl_libs_dir.as_posix()
    py_exe = f"{libdir}/python/310/bin/python.exe" if OS == 'Windows' else\
             f"{libdir}/python/bin/python3.10"

    # USD_PLATFORM_FLAGS
    args = [
        "-D_PXR_CXX_DEFINITIONS=/DBOOST_ALL_NO_LIB",
        "-DPython_FIND_REGISTRY=NEVER",
        f"-DPython3_EXECUTABLE={py_exe}",
    ]
    if build_var == 'debug':
        args += [
            f"-DOIIO_LIBRARIES={libdir}/openimageio/lib/OpenImageIO_d{LIBEXT}^^{libdir}/openimageio/lib/OpenImageIO_util_d{LIBEXT}",
            "-DPXR_USE_DEBUG_PYTHON=ON",
            f"-DOPENVDB_LIBRARY={libdir}/openvdb/lib/openvdb_d.lib",
        ]
    if OS != 'Windows':
        args += [
            f"-DPython3_ROOT_DIR={libdir}/python/",
            f"-DPYTHON_INCLUDE_DIR={libdir}/python/include/python3.10/",
            f"-DPYTHON_LIBRARY={libdir}/tbb/lib/{LIBPREFIX}tbb{LIBEXT}",
        ]
        if OS == 'Darwin':
            args += [
                f'-DCMAKE_SHARED_LINKER_FLAGS=-Xlinker -undefined -Xlinker dynamic_lookup',
            ]

    # DEFAULT_BOOST_FLAGS
    args += [
        f"-DBoost_COMPILER:STRING=-vc142",
        "-DBoost_USE_MULTITHREADED=ON",
        "-DBoost_USE_STATIC_LIBS=OFF",
        "-DBoost_USE_STATIC_RUNTIME=OFF",
        f"-DBOOST_ROOT={libdir}/boost",
        "-DBoost_NO_SYSTEM_PATHS=ON",
        "-DBoost_NO_BOOST_CMAKE=ON",
        "-DBoost_ADDITIONAL_VERSIONS=1.80",
        f"-DBOOST_LIBRARYDIR={libdir}/boost/lib/",
        "-DBoost_USE_DEBUG_PYTHON=On"
    ]

    # USD_EXTRA_ARGS
    args += [
        f"-DOPENSUBDIV_ROOT_DIR={libdir}/opensubdiv",
        f"-DOpenImageIO_ROOT={libdir}/openimageio",
        # f"-DMaterialX_ROOT={libdir}/materialx",
        f"-DMaterialX_DIR={bin_dir / 'materialx/install/lib/cmake/MaterialX'}",
        f"-DOPENEXR_LIBRARIES={libdir}/imath/lib/{LIBPREFIX}Imath{POSTFIX}{LIBEXT}",
        f"-DOPENEXR_INCLUDE_DIR={libdir}/imath/include",
        f"-DImath_DIR={libdir}/imath",
        f"-DOPENVDB_LOCATION={libdir}/openvdb",
        "-DPXR_ENABLE_PYTHON_SUPPORT=ON",
        "-DPXR_USE_PYTHON_3=ON",
        "-DPXR_BUILD_IMAGING=ON",
        "-DPXR_BUILD_TESTS=OFF",
        "-DPXR_BUILD_EXAMPLES=OFF",
        "-DPXR_BUILD_TUTORIALS=OFF",
        "-DPXR_BUILD_USDVIEW=OFF",
        "-DPXR_ENABLE_HDF5_SUPPORT=OFF",
        "-DPXR_ENABLE_MATERIALX_SUPPORT=ON",
        "-DPXR_ENABLE_OPENVDB_SUPPORT=ON",
        f"-DPYTHON_EXECUTABLE={py_exe}",
        "-DPXR_BUILD_MONOLITHIC=ON",
        # OSL is an optional dependency of the Imaging module. However, since that
        # module was included for its support for converting primitive shapes (sphere,
        # cube, etc.) to geometry, it's not necessary. Disabling it will make it
        # simpler to build Blender; currently only Cycles uses OSL.
        "-DPXR_ENABLE_OSL_SUPPORT=OFF",
        # Enable OpenGL for Hydra support. Note that this indirectly also adds an X11
        # dependency on Linux. This would be good to eliminate for headless and Wayland
        # only builds, however is not worse than what Blender already links to for
        # official releases currently.
        "-DPXR_ENABLE_GL_SUPPORT=ON",
        # OIIO is used for loading image textures in Hydra Storm / Embree renderers.
        "-DPXR_BUILD_OPENIMAGEIO_PLUGIN=ON",
        # USD 22.03 does not support OCIO 2.x
        # Tracking ticket https://github.com/PixarAnimationStudios/USD/issues/1386
        "-DPXR_BUILD_OPENCOLORIO_PLUGIN=OFF",
        "-DPXR_ENABLE_PTEX_SUPPORT=OFF",
        "-DPXR_BUILD_USD_TOOLS=OFF",
        "-DCMAKE_DEBUG_POSTFIX=_d",
        "-DBUILD_SHARED_LIBS=ON",
        f"-DTBB_INCLUDE_DIRS={libdir}/tbb/include",
        f"-DTBB_LIBRARIES={libdir}/tbb/lib/{LIBPREFIX}tbb{LIBEXT}",
        f"-DTbb_TBB_LIBRARY={libdir}/tbb/lib/{LIBPREFIX}tbb{LIBEXT}",
        f"-DTBB_tbb_LIBRARY_RELEASE={libdir}/tbb/lib/{LIBPREFIX}tbb{LIBEXT}",
        # USD wants the tbb debug lib set even when you are doing a release build
        # Otherwise it will error out during the cmake configure phase.
        f"-DTBB_LIBRARIES_DEBUG={libdir}/tbb/lib/{LIBPREFIX}tbb{LIBEXT}",
    ]

    cur_dir = os.getcwd()
    os.chdir(str(usd_dir))

    try:
        if git_apply:
            check_call('git', 'apply', '--whitespace=nowarn', str(diff_dir / "usd.diff"))

            # Remove patch after merging https://github.com/PixarAnimationStudios/OpenUSD/pull/2550
            check_call('git', 'apply', '--whitespace=nowarn', str(diff_dir / "usd_opengl_errors_fix.diff"))

        try:
            _cmake(usd_dir, bin_dir / "USD", compiler, jobs, build_var, clean, args)
        finally:
            if git_apply:
                print("Reverting USD repo")
                check_call('git', 'checkout', '--', '*')
                check_call('git', 'clean', '-f')

    finally:
        os.chdir(cur_dir)


def hdrpr(bl_libs_dir, bin_dir, compiler, jobs, clean, build_var, git_apply):
    print_start("Building HdRPR")

    hdrpr_dir = deps_dir / "RadeonProRenderUSD"
    usd_dir = bin_dir / "USD/install"

    libdir = bl_libs_dir.as_posix()

    os.environ['PXR_PLUGINPATH_NAME'] = str(usd_dir / "lib/usd")

    py_exe = f"{libdir}/python/310/bin/python.exe" if OS == 'Windows' \
        else f"{libdir}/python/bin/python3.10"

    # Boost flags
    args = [
        f"-DBoost_COMPILER:STRING=-vc142",
        "-DBoost_USE_MULTITHREADED=ON",
        "-DBoost_USE_STATIC_LIBS=OFF",
        "-DBoost_USE_STATIC_RUNTIME=OFF",
        f"-DBOOST_ROOT={libdir}/boost",
        "-DBoost_NO_SYSTEM_PATHS=ON",
        "-DBoost_NO_BOOST_CMAKE=ON",
        "-DBoost_ADDITIONAL_VERSIONS=1.80",
        f"-DBOOST_LIBRARYDIR={libdir}/boost/lib/",
        f"-DBoost_INCLUDE_DIR={libdir}/boost/include",
        "-DBoost_USE_DEBUG_PYTHON=On"
    ]

    # HdRPR flags
    usd_monolitic_path = f'{usd_dir / "lib" / (f"{LIBPREFIX}usd_ms_d{LIBEXT}" if build_var == "debug" else f"{LIBPREFIX}usd_ms{LIBEXT}")}'

    args += [
        f'-Dpxr_DIR={usd_dir}',
        f"-DMaterialX_DIR={bin_dir / 'materialx/install/lib/cmake/MaterialX'}",
        '-DRPR_BUILD_AS_HOUDINI_PLUGIN=FALSE',
        f'-DPYTHON_EXECUTABLE={py_exe}',
        f"-DOPENEXR_INCLUDE_DIR={libdir}/openexr/include/OpenEXR",
        f"-DOPENEXR_LIBRARIES={libdir}/openexr/lib/{LIBPREFIX}OpenEXR{POSTFIX}{LIBEXT}",
        f"-DImath_DIR={libdir}/imath/lib/cmake/Imath",
        f"-DIMATH_INCLUDE_DIR={libdir}/imath/include/Imath",
        '-DPXR_BUILD_MONOLITHIC=ON',
        f'-DUSD_LIBRARY_DIR={usd_dir / "lib"}',
        f'-DUSD_MONOLITHIC_LIBRARY={usd_monolitic_path}',
        f"-DTBB_INCLUDE_DIR={libdir}/tbb/include",
        f"-DTBB_LIBRARY={libdir}/tbb/lib/{LIBPREFIX}tbb{LIBEXT}",
        f"-DOPENVDB_LOCATION={libdir}/openvdb",
    ]

    # Adding required paths and preloading usd_ms.dll
    paths = [
        usd_dir / 'lib',
        bl_libs_dir / 'boost/lib',
        bl_libs_dir / 'tbb/lib',
        bl_libs_dir / 'openimageio/lib',
        bl_libs_dir / 'openvdb/lib',
        bin_dir / 'materialx/install/bin',
        bl_libs_dir / 'imath/lib',
        bl_libs_dir / 'openexr/lib',
    ]
    pxr_init_py = usd_dir / "lib/python/pxr/__init__.py"
    pxr_init_py_text = None

    if OS == 'Windows':
        print(f"Modifying {pxr_init_py}")
        pxr_init_py_text = pxr_init_py.read_text()
        text_new = pxr_init_py_text
        text_new += f"""

import os
import ctypes

"""
        for p in paths:
            text_new += f'os.add_dll_directory(r"{p}")\n'
        text_new += f'\nctypes.CDLL(r"{usd_dir / "lib/usd_ms.dll"}")\n'
        pxr_init_py.write_text(text_new)

    elif OS == 'Darwin':
        print(f"Modifying {pxr_init_py}")
        pxr_init_py_text = pxr_init_py.read_text()
        text_new = pxr_init_py_text
        text_new += f"""

import ctypes

ctypes.CDLL(r"{bl_libs_dir / 'imath/lib/libImath.dylib'}")
ctypes.CDLL(r"{bl_libs_dir / 'openexr/lib/libOpenEXR.dylib'}")
ctypes.CDLL(r"{bl_libs_dir / 'openexr/lib/libOpenEXRCore.dylib'}")
"""
        pxr_init_py.write_text(text_new)

    else:   # OS == 'Linux':
        os.environ['LD_LIBRARY_PATH'] = ':'.join(str(p) for p in paths)

    cur_dir = os.getcwd()
    ch_dir(hdrpr_dir)
    try:
        if git_apply:
            check_call('git', 'apply', '--whitespace=nowarn', str(diff_dir / "hdrpr_matx.diff"))
            check_call('git', 'apply', '--whitespace=nowarn', str(diff_dir / "hdrpr_libs.diff"))

        try:
            _cmake(hdrpr_dir, bin_dir / "hdrpr", compiler, jobs, build_var, clean, args)
        finally:
            if git_apply:
                print("Reverting HdRPR repo")
                check_call('git', 'checkout', '--', '*')

    finally:
        ch_dir(cur_dir)
        if pxr_init_py_text:
            print(f"Reverting {pxr_init_py}")
            pxr_init_py.write_text(pxr_init_py_text)

    if OS == 'Darwin':
        lib_dir = bin_dir / "hdrpr/install/lib"
        # removing and renaming
        (lib_dir / "libRadeonImageFilters.dylib").unlink()
        (lib_dir / "libRadeonImageFilters.1.dylib").unlink()
        (lib_dir / "libRadeonImageFilters.1.7.3.dylib").rename(lib_dir / "libRadeonImageFilters.dylib")
        check_call('install_name_tool', '-change',
                   "@rpath/libRadeonImageFilters.1.dylib", "@rpath/libRadeonImageFilters.dylib",
                   str(lib_dir / "libRadeonImageFilters.dylib"))
        check_call('install_name_tool', '-change',
                   "@rpath/libRadeonML.0.dylib", "@rpath/libRadeonML.dylib",
                   str(lib_dir / "libRadeonImageFilters.dylib"))

        (lib_dir / "libRadeonML.dylib").unlink()
        (lib_dir / "libRadeonML.0.dylib").unlink()
        (lib_dir / "libRadeonML.0.9.12.dylib").rename(lib_dir / "libRadeonML.dylib")
        check_call('install_name_tool', '-change',
                   "@rpath/libRadeonML.0.dylib", "@rpath/libRadeonML.dylib",
                   str(lib_dir / "libRadeonML.dylib"))

        (lib_dir / "libRadeonML_MPS.dylib").unlink()
        (lib_dir / "libRadeonML_MPS.0.dylib").unlink()
        (lib_dir / "libRadeonML_MPS.0.9.12.dylib").rename(lib_dir / "libRadeonML_MPS.dylib")
        check_call('install_name_tool', '-change',
                   "@rpath/libRadeonML_MPS.0.dylib", "@rpath/libRadeonML_MPS.dylib",
                   str(lib_dir / "libRadeonML_MPS.dylib"))

        # fixing @rpath
        rprusd_lib = bin_dir / "hdrpr/install/lib/librprUsd.dylib"
        assert rprusd_lib.exists()
        check_call('install_name_tool', '-change',
                   "@rpath/libMaterialXFormat.1.dylib", "@rpath/libMaterialXFormat.dylib", str(rprusd_lib))
        check_call('install_name_tool', '-change',
                   "@rpath/libMaterialXCore.1.dylib", "@rpath/libMaterialXCore.dylib", str(rprusd_lib))

        hdrpr_lib = bin_dir / "hdrpr/install/plugin/usd/hdRpr.dylib"
        assert hdrpr_lib.exists()
        check_call('install_name_tool', '-change',
                   "@rpath/libMaterialXFormat.1.dylib", "@rpath/libMaterialXFormat.dylib", str(hdrpr_lib))
        check_call('install_name_tool', '-change',
                   "@rpath/libMaterialXCore.1.dylib", "@rpath/libMaterialXCore.dylib", str(hdrpr_lib))
        check_call('install_name_tool', '-change',
                   "@rpath/libRadeonImageFilters.1.dylib", "@rpath/libRadeonImageFilters.dylib", str(hdrpr_lib))


def zip_addon(bin_dir):
    print_start("Creating zip Addon")

    # region internal functions

    def enumerate_addon_data(bin_dir):
        libs_rel_path = Path('libs/lib')
        plugin_rel_path = Path('libs/plugin/usd/plugin')
        inst_dir = bin_dir / 'install'
        plugin_dir = inst_dir / 'plugin'

        # copy addon scripts
        hydrarpr_plugin_dir = repo_dir / 'src/hydrarpr'
        assert hydrarpr_plugin_dir.exists()
        for f in hydrarpr_plugin_dir.glob("**/*"):
            if f.is_dir():
                continue

            rel_path = f.relative_to(hydrarpr_plugin_dir)
            rel_path_parts = rel_path.parts
            if rel_path_parts[0] in ("libs", "configdev.py", "hdusd.log") or \
                    "__pycache__" in rel_path_parts or ".gitignore" in rel_path_parts:
                continue

            yield f, rel_path

        hydrarpr_repo_dir = deps_dir / "RadeonProRenderUSD"
        assert hydrarpr_repo_dir.exists()

        # copy libraries
        lib_dir = inst_dir / 'lib'
        assert lib_dir.exists()
        for f in lib_dir.glob("**/*"):
            if f.suffix != LIBEXT:
                continue

            yield f, libs_rel_path / f.name

        # copy hdRpr library
        hdrpr_lib = plugin_dir / f"usd/hdRpr{LIBEXT}"
        assert hdrpr_lib.exists()
        yield hdrpr_lib, plugin_rel_path.parent / hdrpr_lib.name

        # copy plugInfo.json library
        pluginfo = plugin_dir / 'plugInfo.json'
        assert pluginfo.exists()
        yield pluginfo, plugin_rel_path.parent.parent / pluginfo.name

        # copy plugin/usd folders
        assert plugin_dir.exists()
        for f in plugin_dir.glob("**/*"):
            rel_path = f.relative_to(plugin_dir.parent)
            if any(p in rel_path.parts for p in ("hdRpr", "rprUsd", 'rprUsdMetadata')):
                yield f, libs_rel_path.parent / rel_path

        # copy python rpr
        pyrpr_dir = bin_dir / 'install/lib/python/rpr'
        assert pyrpr_dir.exists()
        (pyrpr_dir / "RprUsd/__init__.py").write_text("")
        for f in (pyrpr_dir / "__init__.py", pyrpr_dir / "RprUsd/__init__.py"):
            yield f, Path("libs") / f.relative_to(pyrpr_dir.parent.parent)

    def get_version():
        # getting build version
        build_ver = subprocess.getoutput("git rev-parse --short HEAD")

        # # getting plugin version
        # text = (repo_dir / "src/hdusd/__init__.py").read_text()
        # m = re.search(r'"version": \((\d+), (\d+), (\d+)\)', text)
        # plugin_ver = m.group(1), m.group(2), m.group(3)
        #
        # return (*plugin_ver, build_ver)

        return build_ver

    def create_zip_addon(install_dir, bin_dir, name, ver):
        """ Pack addon files to zip archive """
        zip_addon = install_dir / name
        if zip_addon.is_file():
            os.remove(zip_addon)

        print(f"Compressing addon files to: {zip_addon}")
        with zipfile.ZipFile(zip_addon, 'w', compression=zipfile.ZIP_DEFLATED,
                             compresslevel=zlib.Z_BEST_COMPRESSION) as myzip:
            for src, package_path in enumerate_addon_data(bin_dir):
                print(f"adding {src} --> {package_path}")

                arcname = str(Path('hydrarpr') / package_path)

                if str(package_path) == "__init__.py":
                    print(f"    set version_build={ver[3]}")
                    text = src.read_text(encoding='utf-8')
                    text = text.replace('version_build = ""', f'version_build = "{ver[3]}"')
                    myzip.writestr(arcname, text)
                    continue

                myzip.write(str(src), arcname=arcname)

        return zip_addon

    # endregion

    repo_dir = Path(__file__).parent
    install_dir = repo_dir / "install"
    ver = get_version()
    name = f"hydrarpr-{ver}-{OS.lower()}.zip"

    if install_dir.is_dir():
        for file in os.listdir(install_dir):
            if file == name:
                os.remove(install_dir / file)
                break
    else:
        install_dir.mkdir()

    zip_addon = create_zip_addon(install_dir, bin_dir / "hdrpr", name, ver)
    print(f"Addon was compressed to: {zip_addon}")


def main():
    ap = argparse.ArgumentParser()

    # Add the arguments to the parser
    ap.add_argument("-all", required=False, action="store_true",
                    help="Build all")
    ap.add_argument("-materialx", required=False, action="store_true",
                    help="Build MaterialX")
    ap.add_argument("-usd", required=False, action="store_true",
                    help="Build USD")
    ap.add_argument("-hdrpr", required=False, action="store_true",
                    help="Build HdRPR")
    ap.add_argument("-bl-libs-dir", required=False, type=str, default="",
                    help="Path to root of Blender libs directory"),
    ap.add_argument("-bin-dir", required=False, type=str, default="",
                    help="Path to binary directory")
    ap.add_argument("-addon", required=False, action="store_true",
                    help="Create zip addon")
    ap.add_argument("-G", required=False, type=str,
                    help="Compiler for HdRPR and MaterialX in cmake. "
                         'For example: -G "Visual Studio 16 2019" or -G "Xcode"',
                    default="Visual Studio 16 2019" if OS == 'Windows' else "")
    ap.add_argument("-j", required=False, type=int, default=0,
                    help="Number of jobs run in parallel")
    ap.add_argument("-build-var", required=False, type=str, default="release",
                    choices=('release', 'relwithdebuginfo', 'debug'),  # TODO: add 'debug' build variant
                    help="Build variant for USD, HdRPR and dependencies. (default: release)")
    ap.add_argument("-clean", required=False, action="store_true",
                    help="Clean build dirs before start USD or HdRPR build")
    ap.add_argument("-no-git-apply", required=False, action="store_true",
                    help="Do not use `git apply usd.diff for USD repo`")

    args = ap.parse_args()

    bl_libs_dir = Path(args.bl_libs_dir).absolute().resolve()

    bin_dir = Path(args.bin_dir).resolve() if args.bin_dir else (repo_dir / "bin")
    bin_dir = bin_dir.absolute()
    bin_dir.mkdir(parents=True, exist_ok=True)
    global POSTFIX
    if args.build_var == "debug":
        POSTFIX = "_d"

    if args.all or args.materialx:
        materialx(bl_libs_dir, bin_dir, args.G, args.j, args.clean, args.build_var)

    installed_modules = None
    py_exe = str(f"{bl_libs_dir}/python/310/bin/python{POSTFIX}{EXT}") if OS == 'Windows' \
        else str(f"{bl_libs_dir}/python/bin/python3.10{POSTFIX}{EXT}")

    try:
        if args.all or args.usd or args.hdrpr:
            installed_modules = install_requirements(py_exe)

        if args.all or args.usd:
            usd(bl_libs_dir, bin_dir, args.G, args.j, args.clean, args.build_var, not args.no_git_apply)

        if args.all or args.hdrpr:
            hdrpr(bl_libs_dir, bin_dir, args.G, args.j, args.clean, args.build_var, not args.no_git_apply)

    finally:
        if installed_modules:
            uninstall_requirements(py_exe, installed_modules)

    if args.all or args.addon:
        zip_addon(bin_dir)

    print_start("Finished")


if __name__ == "__main__":
    main()
