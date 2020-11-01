import os
import sys

from .. import utils


os.environ['PATH'] = f"{utils.HDUSD_LIBS_DIR / 'usd'};{utils.HDUSD_LIBS_DIR / 'plugins'};" \
                     f"{utils.HDUSD_LIBS_DIR / 'hdrpr'};{os.environ['PATH']}"
os.environ['PXR_PLUGINPATH_NAME'] = str(utils.HDUSD_LIBS_DIR / 'plugins')

sys.path.append(str(utils.HDUSD_LIBS_DIR / 'usd/python'))
