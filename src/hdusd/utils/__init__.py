#**********************************************************************
# Copyright 2020 Advanced Micro Devices, Inc
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#********************************************************************
from pathlib import Path
import tempfile
import os
import shutil
import platform
import sys
import numpy as np
import math

import bpy
import hdusd


# saving current process id
PID = os.getpid()

OS = platform.system()
IS_WIN = OS == 'Windows'
IS_MAC = OS == 'Darwin'
IS_LINUX = OS == 'Linux'

BLENDER_VERSION = f'{bpy.app.version[0]}.{bpy.app.version[1]}'

PLUGIN_ROOT_DIR = Path(hdusd.__file__).parent
BLENDER_ROOT_DIR = (Path(sys.executable).parent / "../Resources") if IS_MAC \
                   else Path(sys.executable).parent
BLENDER_DATA_DIR = next(BLENDER_ROOT_DIR.glob("2.*/datafiles"))

HDUSD_DEBUG_MODE = bool(int(os.environ.get('HDUSD_BLENDER_DEBUG', 0)))
if HDUSD_DEBUG_MODE:
    USD_INSTALL_ROOT = Path(os.environ['USD_INSTALL_ROOT'])
    USD_PLUGIN_ROOT = Path(os.environ['USD_PLUGIN_ROOT'])


from . import logging
log = logging.Log(tag='utils')


def temp_dir():
    """ Returns $TEMP/rprblender temp dir. Creates it if needed """
    d = Path(tempfile.gettempdir()) / "hdusd"
    if not d.is_dir():
        log("Creating temp dir", d)
        d.mkdir()

    return d


def temp_pid_dir():
    """ Returns $TEMP/rprblender/PID temp dir for current process. Creates it if needed """
    d = temp_dir() / str(PID)
    if not d.is_dir():
        log("Creating image temp pid dir", d)
        d.mkdir()

    return d


def get_temp_file(suffix):
    return tempfile.mktemp(suffix=suffix, dir=temp_pid_dir())


def clear_temp_dir():
    """ Clears whole $TEMP/rprblender temp dir """

    d = temp_dir()
    paths = tuple(d.iterdir())
    if not paths:
        return

    log("Clearing temp dir", d)
    for path in paths:
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        else:
            os.remove(path)


def get_data_from_collection(collection, attribute, size, dtype=np.float32):
    len = np.prod(size)
    data = np.zeros(len, dtype=dtype)
    collection.foreach_get(attribute, data)
    return data.reshape(size)


def get_prop_array_data(arr, dtype=np.float32):
    if hasattr(arr, 'foreach_get'):
        data = np.empty(len(arr), dtype=dtype)
        arr.foreach_get(data)
    else:
        data = np.fromiter(arr, dtype=dtype)

    return data


def is_zero(val):
    return np.all(np.isclose(val, 0.0))


def time_str(val):
    """ Convert perfcounter difference to time string minutes:seconds.milliseconds """
    return f"{math.floor(val / 60):02}:{math.floor(val % 60):02}.{math.floor((val % 1) * 100):02}"


def usd_temp_path(*dep_objects):
    h = hash("".join(str(hash(o)) for o in dep_objects)) & 0xffffff
    return temp_pid_dir() / f"tmp{h:x}.usda"
