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
from .utils import logging

logging.limit_log('', level_show_min=logging.INFO)

matlib_url = "https://matlibapi.cistest.luxoft.com/api"
engine_use_preview = True

try:
    # configdev.py example for logging setup:
    # from .utils import logging
    # logging.limit_log('default', logging.DEBUG)
    # from . import config
    # config.<parameter> = True

    from . import configdev
    logging.info('Loaded configdev', tag='')

except ImportError:
    pass
