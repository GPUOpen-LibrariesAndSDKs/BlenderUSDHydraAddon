@echo off
REM ******************************************************************
REM  Copyright 2020 Advanced Micro Devices, Inc
REM  Licensed under the Apache License, Version 2.0 (the "License");
REM  you may not use this file except in compliance with the License.
REM  You may obtain a copy of the License at
REM
REM     http://www.apache.org/licenses/LICENSE-2.0
REM
REM  Unless required by applicable law or agreed to in writing, software
REM  distributed under the License is distributed on an "AS IS" BASIS,
REM  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
REM  See the License for the specific language governing permissions and
REM  limitations under the License.
REM  *******************************************************************
@echo on

:: Submodules
git submodule update --init --recursive

:: USD
python tools\build_usd.py deps\USD ^
    --build deps\USD\build ^
    --no-usdview


:: HdRprPlugin
set PXR_DIR=%CD%\USDPixar
set INSTALL_PREFIX_DIR=%CD%\RPRViewer\binary\windows\inst
cd HdRPRPlugin
cmake -B build -G "Visual Studio 15 2017 Win64" ^
-Dpxr_DIR=%PXR_DIR% ^
-DCMAKE_INSTALL_PREFIX=%INSTALL_PREFIX_DIR% ^
-DRPR_BUILD_AS_HOUDINI_PLUGIN=FALSE ^
-DPXR_USE_PYTHON_3=ON ^
-DMATERIALX_BUILD_PYTHON=ON ^
-DMATERIALX_INSTALL_PYTHON=ON
cmake --build build --config Release --target install
cd ..


:: HdRPR
set PXR_DIR=%CD%\deps\USD
set INSTALL_PREFIX_DIR=%CD%\RPRViewer\binary\windows\inst
pushd .
cd deps\HdRPR

cmake -B build -G "Visual Studio 15 2017 Win64" ^
    -Dpxr_DIR=%PXR_DIR% ^
    -DCMAKE_INSTALL_PREFIX=%INSTALL_PREFIX_DIR% ^
    -DRPR_BUILD_AS_HOUDINI_PLUGIN=FALSE ^
    -DPXR_USE_PYTHON_3=ON ^
    -DMATERIALX_BUILD_PYTHON=ON ^
    -DMATERIALX_INSTALL_PYTHON=ON

cmake -Dpxr_DIR=..\..\USD\build -DCMAKE_INSTALL_PREFIX=..\install ..
cmake --build . --config Release --target install
popd

echo *** Copying libs ***
REM python create_hdusd_libs.py -usd ..\deps\USD\build -hdrpr ..\deps\HdRPR\install -mx d:\pixar\MaterialX\build\installed -libs libs %*