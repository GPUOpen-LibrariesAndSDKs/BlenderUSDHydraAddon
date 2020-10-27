import os
import sys

from .. import utils


if utils.HDUSD_DEBUG_MODE:
    # development configuration uses environment variables to libs and python
    os.environ['PATH'] = f"{utils.USD_INSTALL_ROOT / 'lib'};{utils.USD_INSTALL_ROOT / 'bin'};" \
                         f"{utils.USD_PLUGIN_ROOT / 'lib'};{os.environ['PATH']}"
    os.environ['PXR_PLUGINPATH_NAME'] = str(utils.USD_PLUGIN_ROOT / "plugin")

    sys.path.append(str(utils.USD_INSTALL_ROOT / "lib/python"))
else:
    # use local path
    os.environ['PATH'] = f"{utils.PLUGIN_ROOT_DIR / 'libs/usd'};{utils.PLUGIN_ROOT_DIR / 'libs/plugins'};" \
                         f"{utils.PLUGIN_ROOT_DIR / 'libs/hdrpr'};{os.environ['PATH']}"
    os.environ['PXR_PLUGINPATH_NAME'] = str(utils.PLUGIN_ROOT_DIR / "libs/plugins")

    sys.path.append(str(utils.PLUGIN_ROOT_DIR / "libs/usd/python"))
