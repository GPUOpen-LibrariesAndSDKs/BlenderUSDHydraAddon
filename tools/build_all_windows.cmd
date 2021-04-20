:: ******************************************************************
::  Copyright 2020 Advanced Micro Devices, Inc
::  Licensed under the Apache License, Version 2.0 (the "License");
::  you may not use this file except in compliance with the License.
::  You may obtain a copy of the License at
::
::     http://www.apache.org/licenses/LICENSE-2.0
::
::  Unless required by applicable law or agreed to in writing, software
::  distributed under the License is distributed on an "AS IS" BASIS,
::  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
::  See the License for the specific language governing permissions and
::  limitations under the License.
::  *******************************************************************

:: Submodules
git submodule update --init --recursive

:: USD
python tools\build_usd.py --no-usdview

:: HdRPR
set PXR_DIR=%CD%\bin\USD\install
set INSTALL_DIR=%CD%\bin\HdRPR\install

pushd .
cd deps\HdRPR
cmake -B build -G "Visual Studio 15 2017 Win64" ^
    -Dpxr_DIR=%PXR_DIR% ^
    -DCMAKE_INSTALL_PREFIX=%INSTALL_DIR% ^
    -DRPR_BUILD_AS_HOUDINI_PLUGIN=FALSE
cmake --build build --config Release --target install
popd

:: MaterialX
set INSTALL_DIR=%CD%\bin\MaterialX\install

pushd .
cd deps\HdRPR\deps\MaterialX
cmake -B build -G "Visual Studio 15 2017 Win64" ^
    -DCMAKE_INSTALL_PREFIX=%INSTALL_DIR% ^
    -DMATERIALX_BUILD_PYTHON=ON ^
    -DMATERIALX_BUILD_VIEWER=ON
cmake --build build --config Release --target install
popd

:: Copying libs
python tools\create_libs.py

:: MaterialX classes
python tools\generate_mx_classes.py

:: Zip addon
python tools\create_zip_addon.py