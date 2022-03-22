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
#include "pxr/imaging/hd/engine.h"
#include "pxr/imaging/hd/camera.h"
#include "pxr/imaging/hd/renderPass.h"
#include "pxr/imaging/hd/renderBuffer.h"
#include "pxr/imaging/hd/rprimCollection.h"
#include "pxr/imaging/hd/rendererPlugin.h"
#include "pxr/imaging/hd/rendererPluginRegistry.h"
#include "pxr/imaging/hdx/taskController.h"


#include "pxr/usdImaging/usdImaging/delegate.h"

#include "pxr/usd/usd/stage.h"
#include "pxr/usd/usdGeom/metrics.h"

#include "pxr/base/work/loops.h"

#include "pxr/base/gf/rotation.h"
#include "pxr/base/gf/camera.h"
#include "pxr/base/gf/frustum.h"

#include "renderTask.h"
#include "engine.h"
#include "renderDataDelegate.h"

PXR_NAMESPACE_OPEN_SCOPE

UsdImagingLiteEngine::UsdImagingLiteEngine()
{
}

UsdImagingLiteEngine::~UsdImagingLiteEngine()
{
    _DestroyHydraObjects();
}

bool UsdImagingLiteEngine::SetRendererAov(TfToken const &id)
{
    TF_VERIFY(_renderIndex);
    TF_VERIFY(_renderIndex->IsBprimTypeSupported(HdPrimTypeTokens->renderBuffer));

    SdfPath taskDataDelegateId = _taskDataDelegate->GetDelegateID();
    HdAovDescriptor aovDesc = _renderDelegate->GetDefaultAovDescriptor(id);
    if (aovDesc.format == HdFormatInvalid) {
        TF_RUNTIME_ERROR("Could not set \"%s\" AOV: unsupported by render delegate\n", id.GetText());
        return false;
    }

    SdfPath renderBufferId = taskDataDelegateId.AppendElementString("aov_" + id.GetString());
    _renderIndex->InsertBprim(HdPrimTypeTokens->renderBuffer, _taskDataDelegate.get(), renderBufferId);

    HdRenderBufferDescriptor desc;
    desc.dimensions = GfVec3i(_renderTaskParams.viewport[2] - _renderTaskParams.viewport[0],
                              _renderTaskParams.viewport[3] - _renderTaskParams.viewport[1], 1);
    desc.format = aovDesc.format;
    desc.multiSampled = aovDesc.multiSampled;
    _taskDataDelegate->SetParameter(renderBufferId, _tokens->renderBufferDescriptor, desc);
    _renderIndex->GetChangeTracker().MarkBprimDirty(renderBufferId, HdRenderBuffer::DirtyDescription);

    HdRenderPassAovBinding binding;
    binding.aovName = id;
    binding.renderBufferId = renderBufferId;
    binding.aovSettings = aovDesc.aovSettings;
    _renderTaskParams.aovBindings.push_back(binding);

    return true;
}

bool UsdImagingLiteEngine::GetRendererAov(TfToken const &id, void *buf)
{
    SdfPath renderBufferId = _taskDataDelegate->GetDelegateID().AppendElementString("aov_" + id.GetString());
    HdRenderBuffer *rBuf = static_cast<HdRenderBuffer*>(_renderIndex->GetBprim(HdPrimTypeTokens->renderBuffer, renderBufferId));
    void *data = rBuf->Map();
    memcpy(buf, data, rBuf->GetWidth() * rBuf->GetHeight() * HdDataSizeOfFormat(rBuf->GetFormat()));
    rBuf->Unmap();
    return true;
}

UsdImagingGLRendererSettingsList UsdImagingLiteEngine::GetRendererSettingsList() const
{
    const HdRenderSettingDescriptorList descriptors = _renderDelegate->GetRenderSettingDescriptors();
    UsdImagingGLRendererSettingsList ret;

    for (auto const& desc : descriptors) {
        UsdImagingGLRendererSetting r;
        r.key = desc.key;
        r.name = desc.name;
        r.defValue = desc.defaultValue;

        // Use the type of the default value to tell us what kind of
        // widget to create...
        if (r.defValue.IsHolding<bool>()) {
            r.type = UsdImagingGLRendererSetting::TYPE_FLAG;
        }
        else if (r.defValue.IsHolding<int>() ||
            r.defValue.IsHolding<unsigned int>()) {
            r.type = UsdImagingGLRendererSetting::TYPE_INT;
        }
        else if (r.defValue.IsHolding<float>()) {
            r.type = UsdImagingGLRendererSetting::TYPE_FLOAT;
        }
        else if (r.defValue.IsHolding<std::string>()) {
            r.type = UsdImagingGLRendererSetting::TYPE_STRING;
        }
        else {
            TF_WARN("Setting '%s' with type '%s' doesn't have a UI"
                " implementation...",
                r.name.c_str(),
                r.defValue.GetTypeName().c_str());
            continue;
        }
        ret.push_back(r);
    }

    return ret;
}

VtValue UsdImagingLiteEngine::GetRendererSetting(TfToken const& id) const
{
    return _renderDelegate->GetRenderSetting(id);
}

void UsdImagingLiteEngine::SetRendererSetting(TfToken const& id, VtValue const& value)
{
    _renderDelegate->SetRenderSetting(id, value);
}

void UsdImagingLiteEngine::Render(UsdPrim root, const UsdImagingLiteRenderParams &params)
{
    _sceneDelegate->Populate(root);

    SdfPath renderTaskId = _taskDataDelegate->GetDelegateID().AppendElementString("renderTask");
    _renderIndex->InsertTask<HdRenderTask>(_taskDataDelegate.get(), renderTaskId);

    _taskDataDelegate->SetParameter(renderTaskId, HdTokens->params, _renderTaskParams);
    _renderIndex->GetChangeTracker().MarkTaskDirty(renderTaskId, HdChangeTracker::DirtyParams);

    HdReprSelector reprSelector = HdReprSelector(HdReprTokens->smoothHull);
    HdRprimCollection rprimCollection(HdTokens->geometry, reprSelector, false, TfToken());
    rprimCollection.SetRootPath(SdfPath::AbsoluteRootPath());
    _taskDataDelegate->SetParameter(renderTaskId, HdTokens->collection, rprimCollection);
    _renderIndex->GetChangeTracker().MarkTaskDirty(renderTaskId, HdChangeTracker::DirtyCollection);

    TfTokenVector renderTags{ HdRenderTagTokens->geometry };
    _taskDataDelegate->SetParameter(renderTaskId, HdTokens->renderTags, renderTags);
    _renderIndex->GetChangeTracker().MarkTaskDirty(renderTaskId, HdChangeTracker::DirtyRenderTags);

    std::shared_ptr<HdRenderTask> renderTask = std::static_pointer_cast<HdRenderTask>(_renderIndex->GetTask(renderTaskId));
    HdTaskSharedPtrVector tasks = { renderTask };

    _engine->Execute(_renderIndex.get(), &tasks);
}

void UsdImagingLiteEngine::InvalidateBuffers()
{
}

bool UsdImagingLiteEngine::IsConverged() const
{
    SdfPath renderTaskId = _taskDataDelegate->GetDelegateID().AppendElementString("renderTask");
    std::shared_ptr<HdRenderTask> renderTask = std::static_pointer_cast<HdRenderTask>(_renderIndex->GetTask(renderTaskId));
    return renderTask->IsConverged();
}

void UsdImagingLiteEngine::SetRenderViewport(GfVec4d const & viewport)
{
    _renderTaskParams.viewport = viewport;
}

void UsdImagingLiteEngine::SetCameraPath(SdfPath const & id)
{
}

void UsdImagingLiteEngine::SetCameraState(const GfMatrix4d & viewMatrix, const GfMatrix4d & projectionMatrix)
{
    SdfPath freeCameraId = _taskDataDelegate->GetDelegateID().AppendElementString("freeCamera");
    HdCamera *cam = dynamic_cast<HdCamera *>(_renderIndex->GetSprim(HdPrimTypeTokens->camera, freeCameraId));
    if (cam == nullptr) {
        _renderIndex->InsertSprim(HdPrimTypeTokens->camera, _taskDataDelegate.get(), freeCameraId);
        _taskDataDelegate->SetParameter(freeCameraId, HdCameraTokens->windowPolicy, VtValue(CameraUtilFit));
        _taskDataDelegate->SetParameter(freeCameraId, HdCameraTokens->worldToViewMatrix, VtValue(viewMatrix));
        _taskDataDelegate->SetParameter(freeCameraId, HdCameraTokens->projectionMatrix, VtValue(projectionMatrix));
        _taskDataDelegate->SetParameter(freeCameraId, HdCameraTokens->clipPlanes, VtValue(std::vector<GfVec4d>()));

        _renderTaskParams.camera = freeCameraId;
    }
    else {
        _taskDataDelegate->SetParameter(freeCameraId, HdCameraTokens->worldToViewMatrix, VtValue(viewMatrix));
        _taskDataDelegate->SetParameter(freeCameraId, HdCameraTokens->projectionMatrix, VtValue(projectionMatrix));
        _renderIndex->GetChangeTracker().MarkSprimDirty(freeCameraId, HdCamera::DirtyViewMatrix);
        _renderIndex->GetChangeTracker().MarkSprimDirty(freeCameraId, HdCamera::DirtyProjMatrix);
    }
    
 }

TfTokenVector UsdImagingLiteEngine::GetRendererPlugins()
{
    HfPluginDescVector pluginDescriptors;
    HdRendererPluginRegistry::GetInstance().GetPluginDescs(&pluginDescriptors);

    TfTokenVector pluginsIds;
    for (auto &descr : pluginDescriptors) {
        pluginsIds.push_back(descr.id);
    }
    return pluginsIds;
}

std::string UsdImagingLiteEngine::GetRendererDisplayName(TfToken const & id)
{
    HfPluginDesc pluginDescriptor;
    if (!TF_VERIFY(HdRendererPluginRegistry::GetInstance().GetPluginDesc(id, &pluginDescriptor))) {
        return "";
    }
    return pluginDescriptor.displayName;
}

bool UsdImagingLiteEngine::SetRendererPlugin(TfToken const & id)
{
    HdRendererPluginRegistry& registry = HdRendererPluginRegistry::GetInstance();

    // Special case: id = TfToken() selects the first plugin in the list.
    const TfToken resolvedId = id.IsEmpty() ? registry.GetDefaultPluginId() : id;

    if (_renderDelegate && _renderDelegate.GetPluginId() == resolvedId) {
        return true;
    }

    TF_PY_ALLOW_THREADS_IN_SCOPE();

    HdPluginRenderDelegateUniqueHandle renderDelegate = registry.CreateRenderDelegate(resolvedId);
    if (!renderDelegate) {
        return false;
    }

    const GfMatrix4d rootTransform = _sceneDelegate ? _sceneDelegate->GetRootTransform() : GfMatrix4d(1.0);
    const bool isVisible = _sceneDelegate ? _sceneDelegate->GetRootVisibility() : true;

    _DestroyHydraObjects();

    // Use the new render delegate.
    _renderDelegate = std::move(renderDelegate);

    // Recreate the render index
    _renderIndex.reset(HdRenderIndex::New(_renderDelegate.Get(), {}));

    // Create the new delegate
    _sceneDelegate = std::make_unique<UsdImagingDelegate>(_renderIndex.get(), 
        SdfPath::AbsoluteRootPath().AppendElementString("usdImagingDelegate"));

    _taskDataDelegate = std::make_unique<HdRenderDataDelegate>(_renderIndex.get(),
        SdfPath::AbsoluteRootPath().AppendElementString("taskDataDelegate"));

    // The task context holds on to resources in the render
    // deletegate, so we want to destroy it first and thus
    // create it last.
    _engine = std::make_unique<HdEngine>();

    // Rebuild state in the new delegate/task controller.
    _sceneDelegate->SetRootVisibility(isVisible);
    _sceneDelegate->SetRootTransform(rootTransform);

    return true;
}

bool UsdImagingLiteEngine::IsPauseRendererSupported() const
{
    return false;
}

bool UsdImagingLiteEngine::PauseRenderer()
{
    return false;
}

bool UsdImagingLiteEngine::ResumeRenderer()
{
    return false;
}

bool UsdImagingLiteEngine::StopRenderer()
{
    return false;
}

bool UsdImagingLiteEngine::RestartRenderer()
{
    return _renderDelegate->Restart();
}

void UsdImagingLiteEngine::_DestroyHydraObjects()
{
    // Destroy objects in opposite order of construction.
    _engine = nullptr;
    _taskController = nullptr;
    _taskDataDelegate = nullptr;
    _sceneDelegate = nullptr;
    _renderIndex = nullptr;
    _renderDelegate = nullptr;
}

//----------------------------------------------------------------------------
// Resource Information
//----------------------------------------------------------------------------

VtDictionary UsdImagingLiteEngine::GetRenderStats() const
{
    return _renderDelegate->GetRenderStats();
}

PXR_NAMESPACE_CLOSE_SCOPE

