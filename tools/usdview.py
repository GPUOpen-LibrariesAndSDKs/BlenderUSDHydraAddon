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
LIBS_DIR = Path(__file__).parent.parent / 'libs'

if OS == 'Windows':
    os.environ['PATH'] = f"{LIBS_DIR / 'usd'};{LIBS_DIR / 'plugins/usd'};" \
                         f"{LIBS_DIR / 'hdrpr/lib'};{os.environ['PATH']}"

    if hasattr(os, 'add_dll_directory'):
        os.add_dll_directory(str(LIBS_DIR / 'usd'))
        os.add_dll_directory(str(LIBS_DIR / 'plugins/usd'))
        os.add_dll_directory(str(LIBS_DIR / 'hdrpr/lib'))

os.environ['PXR_PLUGINPATH_NAME'] = str(LIBS_DIR / 'plugins')
os.environ['RPR'] = str(LIBS_DIR / 'hdrpr')

sys.path.append(str(LIBS_DIR / 'usd/python'))
sys.path.append(str(LIBS_DIR / 'hdrpr/lib/python'))
sys.path.append(str(LIBS_DIR / 'materialx/python'))

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
