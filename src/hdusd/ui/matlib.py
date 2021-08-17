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
from . import HdUSD_Panel
from ..utils import matlib


materials = tuple(matlib.Material.get_all_materials())
mat = materials[20]
print(mat)

r = mat.renders[0]
print(r)
r.get_info()
print(r)

p = mat.packages[0]
print(p)
p.get_info()
print(p)


class HDUSD_MATLIB_PT_matlib(HdUSD_Panel):
    bl_label = "Material Library"
    bl_context = "material"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        for mat in matlib.Material.get_all_materials():
            print(mat)


    


