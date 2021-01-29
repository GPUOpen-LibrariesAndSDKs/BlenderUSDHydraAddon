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

#include "pxr/imaging/glf/image.h"

#include "pxr/base/work/loops.h"

#include "pxr/base/gf/rotation.h"
#include "pxr/base/gf/camera.h"
#include "pxr/base/gf/frustum.h"

#include "renderTask.h"
#include "engine.h"
#include "renderDataDelegate.h"

PXR_NAMESPACE_OPEN_SCOPE

HdRenderDelegate* GetRenderDelegate(TfToken const& id) {
    HdRendererPlugin* plugin = nullptr;
    TfToken actualId = id;

    // Special case: TfToken() selects the first plugin in the list.
    if (actualId.IsEmpty()) {
        actualId = HdRendererPluginRegistry::GetInstance().GetDefaultPluginId();
    }
    plugin = HdRendererPluginRegistry::GetInstance().GetRendererPlugin(actualId);

    if (plugin == nullptr) {
        TF_CODING_ERROR("Couldn't find plugin for id %s", actualId.GetText());
        return nullptr;
    } else if (!plugin->IsSupported()) {
        // Don't do anything if the plugin isn't supported on the running
        // system, just return that we're not able to set it.
        HdRendererPluginRegistry::GetInstance().ReleasePlugin(plugin);
        return nullptr;
    }

    HdRenderDelegate* renderDelegate = plugin->CreateRenderDelegate();
    if (!renderDelegate) {
        HdRendererPluginRegistry::GetInstance().ReleasePlugin(plugin);
        return nullptr;
    }

    return renderDelegate;
}

static GfCamera
_ComputeCameraToFrameStage(const UsdStageRefPtr& stage, UsdTimeCode timeCode,
    const TfTokenVector& includedPurposes) {
    // Start with a default (50mm) perspective GfCamera.
    GfCamera gfCamera;
    UsdGeomBBoxCache bboxCache(timeCode, includedPurposes,
        /* useExtentsHint = */ true);
    GfBBox3d bbox = bboxCache.ComputeWorldBound(stage->GetPseudoRoot());
    GfVec3d center = bbox.ComputeCentroid();
    GfRange3d range = bbox.ComputeAlignedRange();
    GfVec3d dim = range.GetSize();
    TfToken upAxis = UsdGeomGetStageUpAxis(stage);
    // Find corner of bbox in the focal plane.
    GfVec2d plane_corner;
    if (upAxis == UsdGeomTokens->y) {
        plane_corner = GfVec2d(dim[0], dim[1]) / 2;
    } else {
        plane_corner = GfVec2d(dim[0], dim[2]) / 2;
    }
    float plane_radius = sqrt(GfDot(plane_corner, plane_corner));
    // Compute distance to focal plane.
    float half_fov = gfCamera.GetFieldOfView(GfCamera::FOVHorizontal) / 2.0;
    float distance = plane_radius / tan(GfDegreesToRadians(half_fov));
    // Back up to frame the front face of the bbox.
    if (upAxis == UsdGeomTokens->y) {
        distance += dim[2] / 2;
    } else {
        distance += dim[1] / 2;
    }
    // Compute local-to-world transform for camera filmback.
    GfMatrix4d xf;
    //if (upAxis == UsdGeomTokens->y) {
        xf.SetTranslate(center + GfVec3d(0, 0, distance));
    /*} else {
        xf.SetRotate(GfRotation(GfVec3d(1, 0, 0), 90));
        xf.SetTranslateOnly(center + GfVec3d(0, -distance, 0));
    }*/
    gfCamera.SetTransform(xf);
    return gfCamera;
}

// Prman linear to display
static float DspyLinearTosRGB(float u) {
    return u < 0.0031308f ? 12.92f * u : 1.055f * powf(u, 0.4167f) - 0.055f;
}

int render_old(UsdPrim root, const UsdImagingLiteRenderParams &params) {
    HdEngine engine;
    auto renderDelegate = GetRenderDelegate(params.renderPluginId);
    auto renderIndex = HdRenderIndex::New(renderDelegate, {});
    auto sceneDelegateId = SdfPath::AbsoluteRootPath().AppendElementString("usdImagingDelegate");
    auto sceneDelegate = new UsdImagingDelegate(renderIndex, sceneDelegateId);
    sceneDelegate->Populate(root);

    renderDelegate->SetRenderSetting(TfToken("maxSamples"), VtValue(params.samples));

    auto taskDataDelegate = new HdRenderDataDelegate(renderIndex, SdfPath::AbsoluteRootPath().AppendElementString("taskDataDelegate"));
    auto taskDataDelegateId = taskDataDelegate->GetDelegateID();

    auto freeCameraId = taskDataDelegateId.AppendElementString("freeCamera");
    renderIndex->InsertSprim(HdPrimTypeTokens->camera, taskDataDelegate, freeCameraId);
    taskDataDelegate->SetParameter(freeCameraId, HdCameraTokens->windowPolicy, VtValue(CameraUtilFit));
    taskDataDelegate->SetParameter(freeCameraId, HdCameraTokens->worldToViewMatrix, VtValue(params.viewMatrix));
    taskDataDelegate->SetParameter(freeCameraId, HdCameraTokens->projectionMatrix, VtValue(params.projMatrix));
    taskDataDelegate->SetParameter(freeCameraId, HdCameraTokens->clipPlanes, VtValue(std::vector<GfVec4d>()));

    GfVec4d viewport(0, 0, params.renderResolution[0], params.renderResolution[1]);
    auto aovDimensions = GfVec3i(params.renderResolution[0], params.renderResolution[1], 1);

    HdRenderPassAovBindingVector aovBindings;
    if (TF_VERIFY(renderIndex->IsBprimTypeSupported(HdPrimTypeTokens->renderBuffer))) {
        for (auto& aov : params.aovs) {
            auto aovDesc = renderDelegate->GetDefaultAovDescriptor(aov);
            if (aovDesc.format != HdFormatInvalid) {
                auto renderBufferId = taskDataDelegateId.AppendElementString("aov_" + aov.GetString());
                renderIndex->InsertBprim(HdPrimTypeTokens->renderBuffer, taskDataDelegate, renderBufferId);

                HdRenderBufferDescriptor desc;
                desc.dimensions = aovDimensions;
                desc.format = aovDesc.format;
                desc.multiSampled = aovDesc.multiSampled;
                taskDataDelegate->SetParameter(renderBufferId, _tokens->renderBufferDescriptor, desc);
                renderIndex->GetChangeTracker().MarkBprimDirty(renderBufferId, HdRenderBuffer::DirtyDescription);

                HdRenderPassAovBinding binding;
                binding.aovName = aov;
                binding.renderBufferId = renderBufferId;
                binding.aovSettings = aovDesc.aovSettings;
                aovBindings.push_back(binding);
            }
            else {
                TF_RUNTIME_ERROR("Could not set \"%s\" AOV: unsupported by render delegate\n", aov.GetText());
            }
        }
    }

    auto renderTaskId = taskDataDelegateId.AppendElementString("renderTask");
    renderIndex->InsertTask<HdRenderTask>(taskDataDelegate, renderTaskId);

    HdRenderTaskParams renderTaskParams;
    renderTaskParams.viewport = viewport;
    renderTaskParams.camera = freeCameraId;
    renderTaskParams.aovBindings = aovBindings;
    taskDataDelegate->SetParameter(renderTaskId, HdTokens->params, renderTaskParams);
    renderIndex->GetChangeTracker().MarkTaskDirty(renderTaskId, HdChangeTracker::DirtyParams);

    auto reprSelector = HdReprSelector(HdReprTokens->smoothHull);
    HdRprimCollection rprimCollection(HdTokens->geometry, reprSelector, false, TfToken());
    rprimCollection.SetRootPath(SdfPath::AbsoluteRootPath());
    taskDataDelegate->SetParameter(renderTaskId, HdTokens->collection, rprimCollection);
    renderIndex->GetChangeTracker().MarkTaskDirty(renderTaskId, HdChangeTracker::DirtyCollection);

    TfTokenVector renderTags{ HdRenderTagTokens->geometry };
    taskDataDelegate->SetParameter(renderTaskId, HdTokens->renderTags, renderTags);
    renderIndex->GetChangeTracker().MarkTaskDirty(renderTaskId, HdChangeTracker::DirtyRenderTags);

    printf("rendering...\n");
    {
        auto renderTask = std::static_pointer_cast<HdRenderTask>(renderIndex->GetTask(renderTaskId));
        HdTaskSharedPtrVector tasks = { renderTask };

        engine.Execute(renderIndex, &tasks);
        while (!renderTask->IsConverged()) {
            printf(".");
            std::this_thread::sleep_for(std::chrono::milliseconds(1000));
        }
    }
    printf("\nrendering finished\n");

    for (auto i = 0; i != params.aovBuffers.size(); i++) {
        void *buf = reinterpret_cast<void *>(params.aovBuffers[i]);
        if (buf == nullptr)
            continue;

        
        HdRenderBuffer *rBuf = static_cast<HdRenderBuffer*>(renderIndex->GetBprim(HdPrimTypeTokens->renderBuffer, aovBindings[i].renderBufferId));
        aovBindings[i].renderBuffer = rBuf;
        void *data = rBuf->Map();
        memcpy(buf, data, rBuf->GetWidth() * rBuf->GetHeight() * HdDataSizeOfFormat(rBuf->GetFormat()));
        rBuf->Unmap();
    }
    printf("results archieved\n");

    delete taskDataDelegate;
    delete sceneDelegate;
    delete renderIndex;
    delete renderDelegate;

    return 0;
}

int render(UsdPrim root, const UsdImagingLiteRenderParams &params) {
    HdEngine engine;
    auto renderDelegate = GetRenderDelegate(params.renderPluginId);
    auto renderIndex = HdRenderIndex::New(renderDelegate, {});

    HdxTaskController *taskController = new HdxTaskController(renderIndex,
        SdfPath::AbsoluteRootPath().AppendElementString("taskController"));

    auto delegate = new UsdImagingDelegate(renderIndex,
        SdfPath::AbsoluteRootPath().AppendElementString("usdImagingDelegate"));

    taskController->SetFreeCameraMatrices(params.viewMatrix, params.projMatrix);
    taskController->SetRenderViewport(GfVec4d(0, 0, params.renderResolution[0], params.renderResolution[1]));
    taskController->SetRenderOutputs(params.aovs);


    delegate->Populate(root);
    delegate->SetTime(params.frame);

    HdTaskSharedPtrVector tasks = taskController->GetRenderingTasks();

    printf("rendering...\n");
    engine.Execute(renderIndex, &tasks);
    while (!taskController->IsConverged()) {
        printf(".");
        std::this_thread::sleep_for(std::chrono::milliseconds(1000));
    }
    printf("\nrendering finished\n");



    for (auto i = 0; i != params.aovBuffers.size(); i++) {
        void *buf = reinterpret_cast<void *>(params.aovBuffers[i]);
        if (buf == nullptr)
            continue;

        HdRenderBuffer *rBuf = taskController->GetRenderOutput(params.aovs[i]);
        void *data = rBuf->Map();
        memcpy(buf, data, rBuf->GetWidth() * rBuf->GetHeight() * HdDataSizeOfFormat(rBuf->GetFormat()));
        rBuf->Unmap();
    }
    printf("results archieved\n");


    delete taskController;
    delete delegate;
    delete renderIndex;
    delete renderDelegate;

    return 0;
}

UsdImagingLiteEngine::UsdImagingLiteEngine()
    : _renderIndex(nullptr)
    , _delegate(nullptr)
    , _rendererPlugin(nullptr)
    , _taskDataDelegate(nullptr)
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

    SdfPath taskDataDelegateId = _taskDataDelegate->GetDelegateID();
    HdAovDescriptor aovDesc = _renderIndex->GetRenderDelegate()->GetDefaultAovDescriptor(id);
    if (aovDesc.format == HdFormatInvalid) {
        TF_RUNTIME_ERROR("Could not set \"%s\" AOV: unsupported by render delegate\n", id.GetText());
        return false;
    }

    SdfPath renderBufferId = taskDataDelegateId.AppendElementString("aov_" + id.GetString());
    _renderIndex->InsertBprim(HdPrimTypeTokens->renderBuffer, _taskDataDelegate, renderBufferId);

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

void UsdImagingLiteEngine::Render(UsdPrim root, const UsdImagingLiteRenderParams & params)
{
    _delegate->Populate(root);

    _renderIndex->GetRenderDelegate()->SetRenderSetting(TfToken("maxSamples"), VtValue(params.samples));

    SdfPath renderTaskId = _taskDataDelegate->GetDelegateID().AppendElementString("renderTask");
    _renderIndex->InsertTask<HdRenderTask>(_taskDataDelegate, renderTaskId);

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

    _engine.Execute(_renderIndex, &tasks);
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
        _renderIndex->InsertSprim(HdPrimTypeTokens->camera, _taskDataDelegate, freeCameraId);
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

    TfTokenVector plugins;
    for (size_t i = 0; i < pluginDescriptors.size(); ++i) {
        plugins.push_back(pluginDescriptors[i].id);
    }
    return plugins;
}

std::string UsdImagingLiteEngine::GetRendererDisplayName(TfToken const & id)
{
    HfPluginDesc pluginDescriptor;
    if (!TF_VERIFY(HdRendererPluginRegistry::GetInstance().
        GetPluginDesc(id, &pluginDescriptor))) {
        return std::string();
    }

    return pluginDescriptor.displayName;
}

bool UsdImagingLiteEngine::SetRendererPlugin(TfToken const & id)
{
    HdRendererPlugin *plugin = nullptr;
    TfToken actualId = id;

    // Special case: TfToken() selects the first plugin in the list.
    if (actualId.IsEmpty()) {
        actualId = HdRendererPluginRegistry::GetInstance().GetDefaultPluginId();
    }
    plugin = HdRendererPluginRegistry::GetInstance().GetRendererPlugin(actualId);

    if (plugin == nullptr) {
        TF_CODING_ERROR("Couldn't find plugin for id %s", actualId.GetText());
        return false;
    }
    if (plugin == _rendererPlugin) {
        // It's a no-op to load the same plugin twice.
        HdRendererPluginRegistry::GetInstance().ReleasePlugin(plugin);
        return true;
    }
    if (!plugin->IsSupported()) {
        // Don't do anything if the plugin isn't supported on the running
        // system, just return that we're not able to set it.
        HdRendererPluginRegistry::GetInstance().ReleasePlugin(plugin);
        return false;
    }

    HdRenderDelegate *renderDelegate = plugin->CreateRenderDelegate();
    if (!renderDelegate) {
        HdRendererPluginRegistry::GetInstance().ReleasePlugin(plugin);
        return false;
    }

    // Pull old delegate/task controller state.
    GfMatrix4d rootTransform = GfMatrix4d(1.0);
    bool isVisible = true;
    if (_delegate != nullptr) {
        rootTransform = _delegate->GetRootTransform();
        isVisible = _delegate->GetRootVisibility();
    }

    // Delete hydra state.
    _DeleteHydraResources();

    // Recreate the render index.
    _rendererPlugin = plugin;
    _rendererId = actualId;

    _renderIndex = HdRenderIndex::New(renderDelegate, {});

    // Create the new delegate & task controller.
    SdfPath delegateId = SdfPath::AbsoluteRootPath().AppendElementString("usdImagingDelegate");
    _delegate = new UsdImagingDelegate(_renderIndex, delegateId);

    _taskDataDelegate = new HdRenderDataDelegate(_renderIndex,
        SdfPath::AbsoluteRootPath().AppendElementString("taskDataDelegate"));

    // Rebuild state in the new delegate/task controller.
    _delegate->SetRootVisibility(isVisible);
    _delegate->SetRootTransform(rootTransform);

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
    return _renderIndex->GetRenderDelegate()->Restart();
}

void UsdImagingLiteEngine::_DeleteHydraResources()
{
    // Unwinding order: remove data sources first (task controller, scene
    // delegate); then render index; then render delegate; finally the
    // renderer plugin used to manage the render delegate.

    if (_taskDataDelegate != nullptr) {
        delete _taskDataDelegate;
        _taskDataDelegate = nullptr;
    }
    if (_delegate != nullptr) {
        delete _delegate;
        _delegate = nullptr;
    }
    HdRenderDelegate *renderDelegate = nullptr;
    if (_renderIndex != nullptr) {
        renderDelegate = _renderIndex->GetRenderDelegate();
        delete _renderIndex;
        _renderIndex = nullptr;
    }
    if (_rendererPlugin != nullptr) {
        if (renderDelegate != nullptr) {
            _rendererPlugin->DeleteRenderDelegate(renderDelegate);
        }
        HdRendererPluginRegistry::GetInstance().ReleasePlugin(_rendererPlugin);
        _rendererPlugin = nullptr;
        _rendererId = TfToken();
    }
}

PXR_NAMESPACE_CLOSE_SCOPE

