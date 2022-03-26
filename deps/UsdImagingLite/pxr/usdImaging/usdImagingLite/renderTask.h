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
#ifndef PXR_USD_IMAGING_USD_IMAGING_LITE_RENDER_TASK_H
#define PXR_USD_IMAGING_USD_IMAGING_LITE_RENDER_TASK_H

#include "pxr/imaging/hd/task.h"
#include "pxr/imaging/hd/renderPass.h"
#include "pxr/imaging/hd/renderPassState.h"

PXR_NAMESPACE_OPEN_SCOPE

class HdRenderTask : public HdTask
{
public:
    HdRenderTask(HdSceneDelegate* delegate, SdfPath const& id);

    HdRenderTask() = delete;
    HdRenderTask(HdRenderTask const&) = delete;
    HdRenderTask &operator=(HdRenderTask const&) = delete;

    ~HdRenderTask() override;

    bool IsConverged() const;

    /// Sync the render pass resources
    void Sync(HdSceneDelegate* delegate,
              HdTaskContext* ctx,
              HdDirtyBits* dirtyBits) override;

    /// Prepare the tasks resources
    void Prepare(HdTaskContext* ctx,
                 HdRenderIndex* renderIndex) override;

    /// Execute render pass task
    void Execute(HdTaskContext* ctx) override;

    /// Collect Render Tags used by the task.
    TfTokenVector const& GetRenderTags() const override;

private:
    HdRenderPassSharedPtr _pass;
    HdRenderPassStateSharedPtr _passState;

    TfTokenVector _renderTags;
    GfVec4d _viewport;
    SdfPath _cameraId;
    HdRenderPassAovBindingVector _aovBindings;
};

struct HdRenderTaskParams
{
    // Should not be empty.
    HdRenderPassAovBindingVector aovBindings;

    SdfPath camera;
    GfVec4d viewport = GfVec4d(0.0);
};

// VtValue requirements
std::ostream& operator<<(std::ostream& out, const HdRenderTaskParams& pv);
bool operator==(const HdRenderTaskParams& lhs, const HdRenderTaskParams& rhs);
bool operator!=(const HdRenderTaskParams& lhs, const HdRenderTaskParams& rhs);

PXR_NAMESPACE_CLOSE_SCOPE

#endif // PXR_USD_IMAGING_USD_IMAGING_LITE_RENDER_TASK_H
