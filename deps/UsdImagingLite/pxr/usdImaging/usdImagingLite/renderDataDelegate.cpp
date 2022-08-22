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
#include "renderDataDelegate.h"

PXR_NAMESPACE_OPEN_SCOPE

HdRenderDataDelegate::HdRenderDataDelegate(HdRenderIndex* parentIndex, SdfPath const& delegateID)
    : HdSceneDelegate(parentIndex, delegateID)
{}

bool HdRenderDataDelegate::HasParameter(SdfPath const& id, TfToken const& key) const
{
    ValueCache vCache;
    if (TfMapLookup(_valueCacheMap, id, &vCache) &&
        vCache.count(key) > 0) {
        return true;
    }
    return false;
}

VtValue HdRenderDataDelegate::Get(SdfPath const& id, TfToken const& key)
{
    auto vcache = TfMapLookupPtr(_valueCacheMap, id);
    VtValue ret;
    if (vcache && TfMapLookup(*vcache, key, &ret)) {
        return ret;
    }
    return VtValue();
}

GfMatrix4d HdRenderDataDelegate::GetTransform(SdfPath const& id)
{
    // We expect this to be called only for the free cam.
    VtValue val = GetCameraParamValue(id, HdTokens->transform);
    return val.Get<GfMatrix4d>();
}

VtValue HdRenderDataDelegate::GetCameraParamValue(SdfPath const& id, TfToken const& key)
{
    return Get(id, key);
}

VtValue HdRenderDataDelegate::GetLightParamValue(SdfPath const& id, TfToken const& paramName)
{
    return Get(id, paramName);
}

HdRenderBufferDescriptor HdRenderDataDelegate::GetRenderBufferDescriptor(SdfPath const& id)
{
    return GetParameter<HdRenderBufferDescriptor>(id, _tokens->renderBufferDescriptor);
}

TfTokenVector HdRenderDataDelegate::GetTaskRenderTags(SdfPath const& taskId)
{
    if (HasParameter(taskId, _tokens->renderTags)) {
        return GetParameter<TfTokenVector>(taskId, _tokens->renderTags);
    }
    return TfTokenVector();
}

PXR_NAMESPACE_CLOSE_SCOPE
