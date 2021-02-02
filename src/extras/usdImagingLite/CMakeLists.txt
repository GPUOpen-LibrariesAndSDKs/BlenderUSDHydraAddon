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
set(PXR_PREFIX pxr/usdImaging)
set(PXR_PACKAGE usdImagingLite)

pxr_library(usdImagingLite
    DISABLE_PRECOMPILED_HEADERS
    LIBRARIES
        garch
        gf
        glf
        sdf
        tf
        usd
        usdGeom
        usdRender
        usdImagingGL
        ${Boost_PYTHON_LIBRARY}

    INCLUDE_DIRS
        ${Boost_INCLUDE_DIRS}
        ../../..

    PUBLIC_CLASSES
        engine
        renderParams

    PUBLIC_HEADERS
        api.h

    PRIVATE_CLASSES
        renderTask
        renderDataDelegate

    PYTHON_CPPFILES
        moduleDeps.cpp

    PYMODULE_CPPFILES
        module.cpp
        wrapEngine.cpp
        wrapRenderParams.cpp

    PYMODULE_FILES
        __init__.py
)
