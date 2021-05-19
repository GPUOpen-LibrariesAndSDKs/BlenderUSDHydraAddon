set(PXR_PREFIX pxr/usdImaging)
set(PXR_PACKAGE usdImagingLite)

pxr_library(usdImagingLite
    DISABLE_PRECOMPILED_HEADERS
    LIBRARIES
        garch
        gf
        glf
        sdf
        tf
        usd
        usdGeom
        usdRender
        usdImagingGL
        ${Boost_PYTHON_LIBRARY}

    INCLUDE_DIRS
        ${Boost_INCLUDE_DIRS}
        ../../..

    PUBLIC_CLASSES
        engine
        renderParams

    PUBLIC_HEADERS
        api.h

    PRIVATE_CLASSES
        renderTask
        renderDataDelegate

    PYTHON_CPPFILES
        moduleDeps.cpp

    PYMODULE_CPPFILES
        module.cpp
        wrapEngine.cpp
        wrapRenderParams.cpp

    PYMODULE_FILES
        __init__.py
)
