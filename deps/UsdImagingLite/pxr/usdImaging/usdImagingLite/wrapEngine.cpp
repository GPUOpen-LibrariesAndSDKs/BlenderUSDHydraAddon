//
// Copyright 2017 Pixar
//
// Licensed under the Apache License, Version 2.0 (the "Apache License")
// with the following modification; you may not use this file except in
// compliance with the Apache License and the following modification to it:
// Section 6. Trademarks. is deleted and replaced with:
//
// 6. Trademarks. This License does not grant permission to use the trade
//    names, trademarks, service marks, or product names of the Licensor
//    and its affiliates, except as required to comply with Section 4(c) of
//    the License and to reproduce the content of the NOTICE file.
//
// You may obtain a copy of the Apache License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the Apache License with the above modification is
// distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
// KIND, either express or implied. See the Apache License for the specific
// language governing permissions and limitations under the Apache License.
//
#include <boost/python/class.hpp>
#include <boost/python/def.hpp>
#include <boost/python/tuple.hpp>
#include <boost/python.hpp>
#include <boost/python/converter/from_python.hpp>

#include "pxr/pxr.h"
#include "engine.h"
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
    {
        using Cls = UsdImagingLiteEngine_wrap;

        scope engineScope = class_<Cls, boost::noncopyable>(
            "Engine", "UsdImaging Lite Renderer class")
            .def(init<>())
            .def("Render", &Cls::Render)
            .def("SetRenderViewport", &Cls::SetRenderViewport)
            .def("SetRendererAov", &Cls::SetRendererAov)
            .def("GetRendererAov", &Cls::GetRendererAov_wrap)
            .def("ClearRendererAovs", &Cls::ClearRendererAovs)
            .def("GetRendererSetting", &Cls::GetRendererSetting)
            .def("SetRendererSetting", &Cls::SetRendererSetting)
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
            .def("GetRenderStats",
                    &Cls::GetRenderStats)
            ;
    }

}
