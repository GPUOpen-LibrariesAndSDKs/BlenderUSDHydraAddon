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
#ifndef PXR_USD_IMAGING_USD_IMAGING_LITE_ENGINE_H
#define PXR_USD_IMAGING_USD_IMAGING_LITE_ENGINE_H

#include "pxr/pxr.h"
#include "pxr/usd/usd/stage.h"

#include "pxr/imaging/hd/engine.h"
#include "pxr/imaging/hd/rendererPlugin.h"
#include "pxr/imaging/hd/pluginRenderDelegateUniqueHandle.h"
#include "pxr/imaging/hdx/taskController.h"
#include "pxr/usdImaging/usdImaging/delegate.h"
#include "pxr/usdImaging/usdImagingGL/rendererSettings.h"

#include "api.h"
#include "renderParams.h"
#include "renderDataDelegate.h"
#include "renderTask.h"

PXR_NAMESPACE_OPEN_SCOPE

/// \class UsdImagingLiteEngine
///
/// The UsdImagingLiteEngine is entry point API for rendering USD scenes for delegates
/// which don't require to use OpenGL. This is more lightweight engine comparing to
/// UsdImagingGLEngine.
///
class UsdImagingLiteEngine
{
public:
    // ---------------------------------------------------------------------
    /// \name Construction
    /// @{
    // ---------------------------------------------------------------------
    USDIMAGINGLITE_API
    UsdImagingLiteEngine();

    // Disallow copies
    UsdImagingLiteEngine(const UsdImagingLiteEngine&) = delete;
    UsdImagingLiteEngine& operator=(const UsdImagingLiteEngine&) = delete;

    USDIMAGINGLITE_API
    ~UsdImagingLiteEngine();

    /// @}

    // ---------------------------------------------------------------------
    /// \name Rendering
    /// @{
    // ---------------------------------------------------------------------

    /// Entry point for kicking off a render
    USDIMAGINGLITE_API
    void Render(UsdPrim root, const UsdImagingLiteRenderParams &params);

    /// Returns true if the resulting image is fully converged.
    /// (otherwise, caller may need to call Render() again to refine the result)
    USDIMAGINGLITE_API
    bool IsConverged() const;

    USDIMAGINGLITE_API
    bool SetRendererAov(TfToken const &id);

    USDIMAGINGLITE_API
    bool GetRendererAov(TfToken const &id, void *buf);

    USDIMAGINGLITE_API
    void ClearRendererAovs();
    /// @}

    /// Returns the list of renderer settings.
    USDIMAGINGLITE_API
    UsdImagingGLRendererSettingsList GetRendererSettingsList() const;

    /// Gets a renderer setting's current value.
    USDIMAGINGLITE_API
    VtValue GetRendererSetting(TfToken const& id) const;

    /// Sets a renderer setting's value.
    USDIMAGINGLITE_API
    void SetRendererSetting(TfToken const& id, VtValue const& value);

    // ---------------------------------------------------------------------
    /// \name Camera State
    /// @{
    // ---------------------------------------------------------------------

    /// Set the viewport to use for rendering as (x,y,w,h), where (x,y)
    /// represents the lower left corner of the viewport rectangle, and (w,h)
    /// is the width and height of the viewport in pixels.
    USDIMAGINGLITE_API
    void SetRenderViewport(GfVec4d const& viewport);

    /// Free camera API
    /// Set camera framing state directly (without pointing to a camera on the 
    /// USD stage). The projection matrix is expected to be pre-adjusted for the
    /// window policy.
    USDIMAGINGLITE_API
    void SetCameraState(const GfMatrix4d& viewMatrix, const GfMatrix4d& projectionMatrix);

    /// @}

    // ---------------------------------------------------------------------
    /// \name Renderer Plugin Management
    /// @{
    // ---------------------------------------------------------------------

    /// Return the vector of available render-graph delegate plugins.
    USDIMAGINGLITE_API
    static TfTokenVector GetRendererPlugins();

    /// Return the user-friendly description of a renderer plugin.
    USDIMAGINGLITE_API
    static std::string GetRendererDisplayName(TfToken const &id);

    /// Set the current render-graph delegate to \p id.
    /// the plugin will be loaded if it's not yet.
    USDIMAGINGLITE_API
    bool SetRendererPlugin(TfToken const &id);

    /// @}

    // ---------------------------------------------------------------------
    /// \name Control of background rendering threads.
    /// @{
    // ---------------------------------------------------------------------

    /// Query the renderer as to whether it supports pausing and resuming.
    USDIMAGINGLITE_API
    bool IsPauseRendererSupported() const;

    /// Pause the renderer.
    ///
    /// Returns \c true if successful.
    USDIMAGINGLITE_API
    bool PauseRenderer();

    /// Resume the renderer.
    ///
    /// Returns \c true if successful.
    USDIMAGINGLITE_API
    bool ResumeRenderer();

    /// Stop the renderer.
    ///
    /// Returns \c true if successful.
    USDIMAGINGLITE_API
    bool StopRenderer();

    /// Restart the renderer.
    ///
    /// Returns \c true if successful.
    USDIMAGINGLITE_API
    bool RestartRenderer();

    /// @}

    // ---------------------------------------------------------------------
    /// \name Render Statistics
    /// @{
    // ---------------------------------------------------------------------

    /// Returns render statistics.
    ///
    /// The contents of the dictionary will depend on the current render
    /// delegate.
    ///
    USDIMAGINGLITE_API
    VtDictionary GetRenderStats() const;

    /// @}

private:
    std::unique_ptr<HdRenderIndex> _renderIndex;
    HdPluginRenderDelegateUniqueHandle _renderDelegate;
    std::unique_ptr<UsdImagingDelegate> _sceneDelegate;
    std::unique_ptr<HdRenderDataDelegate> _renderDataDelegate;
    std::unique_ptr<HdEngine> _engine;

    HdRenderPassAovBindingVector _aovBindings;
    HdRenderTaskParams _renderTaskParams;

    bool _isPopulated;
    HdRprimCollection _renderCollection;

    // This function disposes of: the render index, the render plugin,
    // the task controller, and the usd imaging delegate.
    void _DeleteHydraResources();


};

PXR_NAMESPACE_CLOSE_SCOPE

#endif // PXR_USD_IMAGING_USD_IMAGING_LITE_ENGINE_H
