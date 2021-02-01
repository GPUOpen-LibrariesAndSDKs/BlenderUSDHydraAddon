/**********************************************************************
* Copyright 2020 Advanced Micro Devices, Inc
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
*     http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
********************************************************************/
#include <boost/python/class.hpp>
#include <boost/python/def.hpp>
#include <boost/python/tuple.hpp>
#include <boost/python.hpp>
#include <boost/python/converter/from_python.hpp>

#include "renderParams.h"

using namespace boost::python;

PXR_NAMESPACE_USING_DIRECTIVE

void
wrapRenderParams()
{
    // Wrap the UsdImagingLiteRenderParams struct. Accessible as 
    // UsdImagingLite.RenderParams
    using Params = UsdImagingLiteRenderParams;
    class_<UsdImagingLiteRenderParams>("RenderParams", "Render parameters")
        .def_readwrite("renderPluginId", &Params::renderPluginId)
        .def_readwrite("frame", &Params::frame)
        .def_readwrite("samples", &Params::samples)
        .def_readwrite("colorCorrectionMode", &Params::colorCorrectionMode)
        .def_readwrite("clearColor", &Params::clearColor)
        .def_readwrite("renderResolution", &Params::renderResolution)
        .def_readwrite("viewMatrix", &Params::viewMatrix)
        .def_readwrite("projMatrix", &Params::projMatrix)
        .def_readwrite("aovs", &Params::aovs)
        .def_readwrite("aovBuffers", &Params::aovBuffers)
        ;
}
