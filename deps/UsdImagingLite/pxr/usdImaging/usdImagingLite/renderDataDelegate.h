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
#ifndef PXR_USD_IMAGING_USD_IMAGING_LITE_RENDER_DATA_DELEGATE_H
#define PXR_USD_IMAGING_USD_IMAGING_LITE_RENDER_DATA_DELEGATE_H

#include "pxr/pxr.h"
#include "pxr/imaging/hd/camera.h"
#include "pxr/imaging/hd/sceneDelegate.h"
#include "pxr/imaging/hd/renderIndex.h"
#include "pxr/usd/usd/stage.h"


PXR_NAMESPACE_OPEN_SCOPE

TF_DEFINE_PRIVATE_TOKENS(_tokens,
    (renderBufferDescriptor)
    (renderTags));

class HdRenderDataDelegate : public HdSceneDelegate {
public:
    HdRenderDataDelegate(HdRenderIndex* parentIndex, SdfPath const& delegateID);
    ~HdRenderDataDelegate() override = default;

    template <typename T>
    void SetParameter(SdfPath const& id, TfToken const& key, T const& value)
    {
        _valueCacheMap[id][key] = value;
    }

    template <typename T>
    T const& GetParameter(SdfPath const& id, TfToken const& key) const
    {
        VtValue vParams;
        ValueCache vCache;
        TF_VERIFY(
            TfMapLookup(_valueCacheMap, id, &vCache) &&
            TfMapLookup(vCache, key, &vParams) &&
            vParams.IsHolding<T>());
        return vParams.Get<T>();
    }

    bool HasParameter(SdfPath const& id, TfToken const& key) const;
    VtValue Get(SdfPath const& id, TfToken const& key) override;
    GfMatrix4d GetTransform(SdfPath const& id) override;
    VtValue GetCameraParamValue(SdfPath const& id, TfToken const& key) override;
    VtValue GetLightParamValue(SdfPath const& id, TfToken const& paramName) override;
    HdRenderBufferDescriptor GetRenderBufferDescriptor(SdfPath const& id) override;
    TfTokenVector GetTaskRenderTags(SdfPath const& taskId) override;

private:
    typedef TfHashMap<TfToken, VtValue, TfToken::HashFunctor> ValueCache;
    typedef TfHashMap<SdfPath, ValueCache, SdfPath::Hash> ValueCacheMap;
    ValueCacheMap _valueCacheMap;
};

PXR_NAMESPACE_CLOSE_SCOPE

#endif // PXR_USD_IMAGING_USD_IMAGING_LITE_RENDER_DATA_DELEGATE_H
