# Copyright 2016 Pixar
#
# Licensed under the Apache License, Version 2.0 (the "Apache License")
# with the following modification; you may not use this file except in
# compliance with the Apache License and the following modification to it:
# Section 6. Trademarks. is deleted and replaced with:
#
# 6. Trademarks. This License does not grant permission to use the trade
#    names, trademarks, service marks, or product names of the Licensor
#    and its affiliates, except as required to comply with Section 4(c) of
#    the License and to reproduce the content of the NOTICE file.
#
# You may obtain a copy of the Apache License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the Apache License with the above modification is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied. See the Apache License for the specific
# language governing permissions and limitations under the Apache License.
#

from __future__ import print_function
import sys
import platform
import os
from pathlib import Path


OS = platform.system()
PYTHON_VERSION = f'{sys.version_info.major}.{sys.version_info.minor}'
LIBS_DIR = Path(__file__).parent.parent / f'libs-{PYTHON_VERSION}'


if OS == 'Windows':
    path_str = ""
    for loc_path in ('lib', 'bin', 'plugin/usd'):
        path = LIBS_DIR / loc_path
        os.add_dll_directory(str(path))
        path_str += f"{path};"

    os.environ['PATH'] = path_str + os.environ['PATH']

os.environ['PXR_PLUGINPATH_NAME'] = str(LIBS_DIR / 'plugin')
os.environ['RPR'] = str(LIBS_DIR)

sys.path.append(str(LIBS_DIR / 'lib/python'))
sys.path.append(str(LIBS_DIR / 'python'))

from pxr import Usdviewq


if __name__ == '__main__':
    # Let Ctrl-C kill the app.
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    try:
        Usdviewq.Launcher().Run()

    except Usdviewq.InvalidUsdviewOption as e:
        print("ERROR: " + e.message, file=sys.stderr)
        sys.exit(1)
