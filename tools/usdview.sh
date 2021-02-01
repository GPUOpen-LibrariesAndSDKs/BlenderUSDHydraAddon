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

export LD_LIBRARY_PATH=$HDUSD_LIBS_DIR/usd:$HDUSD_LIBS_DIR/plugins:$HDUSD_LIBS_DIR/hdrpr/lib:$LD_LIBRARY_PATH
export PXR_PLUGINPATH_NAME=$HDUSD_LIBS_DIR/plugins
export RPR=$HDUSD_LIBS_DIR/hdrpr
export PYTHONPATH=$PYTHONPATH:$HDUSD_LIBS_DIR/usd/python:$HDUSD_LIBS_DIR/materialx/python:$HDUSD_LIBS_DIR/hdrpr/lib/python

$HDUSD_LIBS_DIR/usd/usdview "$@"
