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
BLENDER_DATA_DIR = Path(bpy.utils.resource_path('LOCAL'))

HDUSD_DEBUG_MODE = bool(int(os.environ.get('HDUSD_BLENDER_DEBUG', 0)))
HDUSD_LIBS_DIR = Path(os.environ['HDUSD_LIBS_DIR']) if HDUSD_DEBUG_MODE else \
                 PLUGIN_ROOT_DIR / 'libs'


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
    return Path(tempfile.mktemp(suffix, "tmp", temp_pid_dir()))


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


def time_str(val):
    """ Convert perfcounter difference to time string minutes:seconds.milliseconds """
    return f"{math.floor(val / 60):02}:{math.floor(val % 60):02}.{math.floor((val % 1) * 100):02}"


def depsgraph_objects(depsgraph, space_data=None, use_scene_lights=True):
    for obj in depsgraph.objects:
        if obj.type not in ('MESH', 'LIGHT', 'CURVE', 'FONT',
                            'SURFACE', 'META', 'VOLUME', 'CAMERA'):
            continue

        if obj.type == 'LIGHT' and not use_scene_lights:
            continue

        if space_data and not obj.visible_in_viewport_get(space_data):
            continue

        yield obj


def title_str(str):
    return str.replace('_', ' ').title()


def code_str(str):
    return str.replace(' ', '_').replace('.', '_').lower()


def set_mx_param_value(mx_param, val, nd_type):
    import MaterialX as mx

    if isinstance(val, mx.Node):
        mx_param.setNodeName(val.getName())
    elif nd_type == 'filename':
        mx_param.setValueString(val)
    else:
        mx_type = getattr(mx, title_str(nd_type), None)
        if mx_type:
            mx_param.setValue(mx_type(val))
        else:
            mx_param.setValue(val)
