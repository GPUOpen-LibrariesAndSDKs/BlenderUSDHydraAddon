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
#ifndef PXR_USD_IMAGING_USD_IMAGING_LITE_RENDER_PARAMS_H
#define PXR_USD_IMAGING_USD_IMAGING_LITE_RENDER_PARAMS_H

#include "pxr/pxr.h"
#include "api.h"

#include "pxr/usd/usd/timeCode.h"

#include "pxr/base/gf/vec2i.h"
#include "pxr/base/gf/vec4d.h"
#include "pxr/base/gf/vec4f.h"
#include "pxr/base/gf/matrix4d.h"
#include "pxr/base/tf/token.h"

PXR_NAMESPACE_OPEN_SCOPE

/// \class UsdImagingLiteRenderParams
///
/// Used as an arguments class for various methods in UsdImagingLiteEngine.
///
class UsdImagingLiteRenderParams 
{
public:
    TfToken renderPluginId;
    UsdTimeCode frame;
    int samples;
    GfVec4f clearColor;
    TfToken colorCorrectionMode;
    GfVec2i renderResolution;
    GfMatrix4d viewMatrix;
    GfMatrix4d projMatrix;
    TfTokenVector aovs;
    std::vector<int64_t> aovBuffers;

    inline UsdImagingLiteRenderParams();

    inline bool operator==(const UsdImagingLiteRenderParams &other) const;

    inline bool operator!=(const UsdImagingLiteRenderParams &other) const {
        return !(*this == other);
    }
};

UsdImagingLiteRenderParams::UsdImagingLiteRenderParams()
    : renderPluginId("HdRprPlugin")
    , frame(UsdTimeCode::Default())
    , samples(64)
    , clearColor(0, 0, 0, 1)
    , renderResolution(100, 100)
{
}

bool UsdImagingLiteRenderParams::operator==(const UsdImagingLiteRenderParams &other) const {
    return renderPluginId == other.renderPluginId
        && frame == other.frame
        && clearColor == other.clearColor
        && colorCorrectionMode == other.colorCorrectionMode
        && renderResolution == other.renderResolution
        && viewMatrix == other.viewMatrix
        && projMatrix == other.projMatrix
        && aovs == other.aovs
        && aovBuffers == other.aovBuffers;
}

PXR_NAMESPACE_CLOSE_SCOPE

#endif // PXR_USD_IMAGING_USD_IMAGING_LITE_RENDER_PARAMS_H
