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
#ifndef PXR_USD_IMAGING_USD_IMAGING_LITE_RENDER_PARAMS_H
#define PXR_USD_IMAGING_USD_IMAGING_LITE_RENDER_PARAMS_H

#include "pxr/pxr.h"
#include "pxr/usdImaging/usdImagingLite/api.h"

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
