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
    : _isPopulated(false)
{
}

UsdImagingLiteEngine::~UsdImagingLiteEngine()
{
    _DeleteHydraResources();
}

bool UsdImagingLiteEngine::SetRendererAov(TfToken const &id)
{
    TF_VERIFY(_renderIndex);
    TF_VERIFY(_renderIndex->IsBprimTypeSupported(HdPrimTypeTokens->renderBuffer));

    HdAovDescriptor aovDesc = _renderDelegate->GetDefaultAovDescriptor(id);
    if (aovDesc.format == HdFormatInvalid) {
        TF_RUNTIME_ERROR("Could not set \"%s\" AOV: unsupported by render delegate\n", id.GetText());
        return false;
    }

    SdfPath renderBufferId = _renderDataDelegate->GetDelegateID().AppendElementString("aov_" + id.GetString());
    _renderIndex->InsertBprim(HdPrimTypeTokens->renderBuffer, _renderDataDelegate.get(), renderBufferId);

    HdRenderBufferDescriptor desc;
    desc.dimensions = GfVec3i(_renderTaskParams.viewport[2] - _renderTaskParams.viewport[0],
                              _renderTaskParams.viewport[3] - _renderTaskParams.viewport[1], 1);
    desc.format = aovDesc.format;
    desc.multiSampled = aovDesc.multiSampled;
    _renderDataDelegate->SetParameter(renderBufferId, _tokens->renderBufferDescriptor, desc);
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
    SdfPath renderBufferId = _renderDataDelegate->GetDelegateID().AppendElementString("aov_" + id.GetString());
    HdRenderBuffer *rBuf = static_cast<HdRenderBuffer*>(_renderIndex->GetBprim(HdPrimTypeTokens->renderBuffer, renderBufferId));
    void *data = rBuf->Map();
    memcpy(buf, data, rBuf->GetWidth() * rBuf->GetHeight() * HdDataSizeOfFormat(rBuf->GetFormat()));
    rBuf->Unmap();
    return true;
}

void UsdImagingLiteEngine::ClearRendererAovs()
{
    TF_VERIFY(_renderIndex);

    for (HdRenderPassAovBinding& binding : _renderTaskParams.aovBindings) {
        _renderIndex->RemoveBprim(HdPrimTypeTokens->renderBuffer, binding.renderBufferId);
    }
    _renderTaskParams.aovBindings.clear();
}

VtValue UsdImagingLiteEngine::GetRendererSetting(TfToken const& id) const
{
    TF_VERIFY(_renderDelegate);
    return _renderDelegate->GetRenderSetting(id);
}

void UsdImagingLiteEngine::SetRendererSetting(TfToken const& id, VtValue const& value)
{
    TF_VERIFY(_renderDelegate);
    _renderDelegate->SetRenderSetting(id, value);
}

void UsdImagingLiteEngine::Render(UsdPrim root, const UsdImagingLiteRenderParams &params)
{
    TF_VERIFY(_sceneDelegate);

    if (!_isPopulated) {
        _sceneDelegate->Populate(root);
        _isPopulated = true;
    }

    // SetTime will only react if time actually changes.
    _sceneDelegate->SetTime(params.frame);

    SdfPath renderTaskId = _renderDataDelegate->GetDelegateID().AppendElementString("renderTask");
    _renderIndex->InsertTask<HdRenderTask>(_renderDataDelegate.get(), renderTaskId);
    std::shared_ptr<HdRenderTask> renderTask = std::static_pointer_cast<HdRenderTask>(_renderIndex->GetTask(renderTaskId));

    _renderDataDelegate->SetParameter(renderTaskId, HdTokens->params, _renderTaskParams);
    _renderIndex->GetChangeTracker().MarkTaskDirty(renderTaskId, HdChangeTracker::DirtyParams);

    HdReprSelector reprSelector = HdReprSelector(HdReprTokens->smoothHull);
    HdRprimCollection rprimCollection(HdTokens->geometry, reprSelector, false, TfToken());
    rprimCollection.SetRootPath(SdfPath::AbsoluteRootPath());
    _renderDataDelegate->SetParameter(renderTaskId, HdTokens->collection, rprimCollection);
    _renderIndex->GetChangeTracker().MarkTaskDirty(renderTaskId, HdChangeTracker::DirtyCollection);

    TfTokenVector renderTags{ HdRenderTagTokens->geometry };
    _renderDataDelegate->SetParameter(renderTaskId, HdTokens->renderTags, renderTags);
    _renderIndex->GetChangeTracker().MarkTaskDirty(renderTaskId, HdChangeTracker::DirtyRenderTags);

    HdTaskSharedPtrVector tasks = { renderTask };
    {
        // Release the GIL before calling into hydra, in case any hydra plugins
        // call into python.
        TF_PY_ALLOW_THREADS_IN_SCOPE();
        _engine->Execute(_renderIndex.get(), &tasks);
    }
}

bool UsdImagingLiteEngine::IsConverged() const
{
    TF_VERIFY(_renderIndex);

    std::shared_ptr<HdRenderTask> renderTask = std::static_pointer_cast<HdRenderTask>(_renderIndex->GetTask(
        _renderDataDelegate->GetDelegateID().AppendElementString("renderTask")));
    return renderTask->IsConverged();
}

void UsdImagingLiteEngine::SetRenderViewport(GfVec4d const & viewport)
{
    _renderTaskParams.viewport = viewport;
}

void UsdImagingLiteEngine::SetCameraState(const GfMatrix4d & viewMatrix, const GfMatrix4d & projectionMatrix)
{
    TF_VERIFY(_renderIndex);

    SdfPath freeCameraId = _renderDataDelegate->GetDelegateID().AppendElementString("freeCamera");
    if (_renderIndex->GetSprim(HdPrimTypeTokens->camera, freeCameraId)) {
        _renderIndex->RemoveSprim(HdPrimTypeTokens->camera, freeCameraId);
    }
    _renderIndex->InsertSprim(HdPrimTypeTokens->camera, _renderDataDelegate.get(), freeCameraId);
    _renderDataDelegate->SetParameter(freeCameraId, HdCameraTokens->windowPolicy, VtValue(CameraUtilFit));
    _renderDataDelegate->SetParameter(freeCameraId, HdCameraTokens->worldToViewMatrix, VtValue(viewMatrix));
    _renderDataDelegate->SetParameter(freeCameraId, HdCameraTokens->projectionMatrix, VtValue(projectionMatrix));
    _renderDataDelegate->SetParameter(freeCameraId, HdCameraTokens->clipPlanes, VtValue(std::vector<GfVec4d>()));

    _renderTaskParams.camera = freeCameraId;
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

    _DeleteHydraResources();

    _isPopulated = false;

    // Use the new render delegate.
    _renderDelegate = std::move(renderDelegate);

    // Recreate the render index
    _renderIndex.reset(HdRenderIndex::New(_renderDelegate.Get(), {}));

    // Create the new delegate
    _sceneDelegate = std::make_unique<UsdImagingDelegate>(_renderIndex.get(), 
        SdfPath::AbsoluteRootPath().AppendElementString("usdImagingDelegate"));

    _renderDataDelegate = std::make_unique<HdRenderDataDelegate>(_renderIndex.get(),
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
    TF_VERIFY(_renderDelegate);
    return _renderDelegate->IsPauseSupported();
}

bool UsdImagingLiteEngine::PauseRenderer()
{
    TF_PY_ALLOW_THREADS_IN_SCOPE();

    TF_VERIFY(_renderDelegate);
    return _renderDelegate->Pause();
}

bool UsdImagingLiteEngine::ResumeRenderer()
{
    TF_PY_ALLOW_THREADS_IN_SCOPE();

    TF_VERIFY(_renderDelegate);
    return _renderDelegate->Resume();
}

bool UsdImagingLiteEngine::StopRenderer()
{
    TF_PY_ALLOW_THREADS_IN_SCOPE();

    TF_VERIFY(_renderDelegate);
    return _renderDelegate->Stop();
}

bool UsdImagingLiteEngine::RestartRenderer()
{
    TF_PY_ALLOW_THREADS_IN_SCOPE();

    TF_VERIFY(_renderDelegate);
    return _renderDelegate->Restart();
}

void UsdImagingLiteEngine::_DeleteHydraResources()
{
    // Destroy objects in opposite order of construction.
    _engine = nullptr;
    _renderDataDelegate = nullptr;
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
