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

#include "pxr/pxr.h"
#include "pxr/usdImaging/usdImagingLite/engine.h"
#include "pxr/base/tf/pyContainerConversions.h"
#include "pxr/base/tf/pyResultConversions.h"


using namespace boost::python;


PXR_NAMESPACE_USING_DIRECTIVE


class UsdImagingLiteEngine_wrap : public UsdImagingLiteEngine
{
public:
    bool GetRendererAov_wrap(TfToken const &id, int64_t buf_ptr)
    {
        return GetRendererAov(id, reinterpret_cast<void *>(buf_ptr));
    }
};

void
wrapEngine()
{
    def(
        "Render",
        render,
        (args("root", "params")));

    {
        using Cls = UsdImagingLiteEngine_wrap;

        scope engineScope = class_<Cls, boost::noncopyable>(
            "Engine", "UsdImaging Lite Renderer class")
            .def(init<>())
            .def("Render", &Cls::Render)
            .def("SetRenderViewport", &Cls::SetRenderViewport)
            .def("SetRendererAov", &Cls::SetRendererAov)
            .def("GetRendererAov", &Cls::GetRendererAov_wrap)
            .def("SetCameraPath", &Cls::SetCameraPath)
            .def("SetCameraState", &Cls::SetCameraState)
            .def("IsConverged", &Cls::IsConverged)
            .def("GetRendererDisplayName", &Cls::GetRendererDisplayName)
            .staticmethod("GetRendererDisplayName")
            .def("SetRendererPlugin", &Cls::SetRendererPlugin)
            .def("IsPauseRendererSupported", &Cls::IsPauseRendererSupported)
            .def("PauseRenderer", &Cls::PauseRenderer)
            .def("ResumeRenderer", &Cls::ResumeRenderer)
            .def("StopRenderer", &Cls::StopRenderer)
            .def("RestartRenderer", &Cls::RestartRenderer)
            .def("GetRendererPlugins", &Cls::GetRendererPlugins,
                return_value_policy< TfPySequenceToList >())
            .staticmethod("GetRendererPlugins")
            ;
    }

}
