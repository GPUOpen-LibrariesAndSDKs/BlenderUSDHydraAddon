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

set PATH=%HDUSD_LIBS_DIR%\usd;%HDUSD_LIBS_DIR%\plugins;%HDUSD_LIBS_DIR%\hdrpr\lib;%PATH%
set PXR_PLUGINPATH_NAME=%HDUSD_LIBS_DIR%\plugins
set RPR=%HDUSD_LIBS_DIR%\hdrpr
set PYTHONPATH=%PYTHONPATH%;%HDUSD_LIBS_DIR%\usd\python;%HDUSD_LIBS_DIR%\materialx\python;%HDUSD_LIBS_DIR%\hdrpr\lib\python

%HDUSD_LIBS_DIR%\usd\usdview.cmd %*
