set PATH=%HDUSD_LIBS_DIR%\usd;%HDUSD_LIBS_DIR%\plugins;%HDUSD_LIBS_DIR%\hdrpr\lib;%PATH%
set PXR_PLUGINPATH_NAME=%HDUSD_LIBS_DIR%\plugins
set RPR=%HDUSD_LIBS_DIR%\hdrpr
set PYTHONPATH=%PYTHONPATH%;%HDUSD_LIBS_DIR%\usd\python;%HDUSD_LIBS_DIR%\materialx\python;%HDUSD_LIBS_DIR%\hdrpr\lib\python

%HDUSD_LIBS_DIR%\usd\usdview.cmd %*
