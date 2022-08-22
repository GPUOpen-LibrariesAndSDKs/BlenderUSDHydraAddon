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
from dataclasses import dataclass
import numpy as np
import math

from pxr import UsdGeom, Sdf, UsdShade, Vt, Tf
import bpy
import bmesh
import mathutils

from . import material
from ..utils import get_data_from_collection

from ..utils import logging
log = logging.Log('export.mesh')


@dataclass(init=False)
class MeshData:
    """ Dataclass which holds all mesh settings. It is used also for area lights creation """

    vertices: np.array
    normals: np.array
    uv_layers: dir
    uv_indices: np.array
    vertex_indices: np.array
    normal_indices: np.array
    num_face_vertices: np.array
    vertex_colors: np.array = None
    area: float = None

    @staticmethod
    def init_from_mesh(mesh: bpy.types.Mesh, calc_area=False, obj=None):
        """ Returns MeshData from bpy.types.Mesh """

        # Looks more like Blender's bug that we have to check that mesh has calc_normals_split().
        # It is possible after deleting corresponded object with such mesh from the scene.
        if not hasattr(mesh, 'calc_normals_split'):
            log.warn("No calc_normals_split() in mesh", mesh)
            return None

        # preparing mesh to export
        mesh.calc_normals_split()
        mesh.calc_loop_triangles()

        # getting mesh export data
        tris_len = len(mesh.loop_triangles)
        if tris_len == 0:
            return None

        data = MeshData()
        data.vertices = get_data_from_collection(mesh.vertices, 'co', (len(mesh.vertices), 3))

        len_loop_triangles = len(mesh.loop_triangles)
        data.normals = get_data_from_collection(mesh.loop_triangles, 'split_normals',
                                                (len_loop_triangles * 3, 3))

        data.uv_layers = {}
        data.uv_indices = None
        for uv_layer in mesh.uv_layers:
            uvs = get_data_from_collection(uv_layer.data, 'uv', (len(uv_layer.data), 2))
            uv_indices = get_data_from_collection(mesh.loop_triangles, 'loops',
                                                  (len_loop_triangles * 3,), np.int32)
            if len(uvs) > 0:
                data.uv_layers[uv_layer.name] = (uvs, uv_indices)
                data.uv_indices = uv_indices

        data.num_face_vertices = np.full((tris_len,), 3, dtype=np.int32)
        data.vertex_indices = get_data_from_collection(mesh.loop_triangles, 'vertices',
                                                       (len_loop_triangles * 3,), np.int32)
        data.normal_indices = np.arange(tris_len * 3, dtype=np.int32)

        if calc_area:
            data.area = sum(tri.area for tri in mesh.loop_triangles)

        # set active vertex color map
        if mesh.vertex_colors.active:
            color_data = mesh.vertex_colors.active.data
            # getting vertex colors and its indices (the same as uv_indices)
            colors = get_data_from_collection(color_data, 'color', (len(color_data), 4))
            color_indices = data.uv_indices[0] if (data.uv_indices is not None and len(data.uv_indices) > 0) else \
                get_data_from_collection(mesh.loop_triangles, 'loops',
                                         (len_loop_triangles * 3,), np.int32)

            # preparing vertex_color buffer with the same size as vertices and
            # setting its data by indices from vertex colors
            if colors[color_indices].size > 0:
                data.vertex_colors = np.zeros((len(data.vertices), 4), dtype=np.float32)
                data.vertex_colors[data.vertex_indices] = colors[color_indices]

        return data

    @staticmethod
    def init_from_shape_type(shape_type, size, size_y, segments):
        """
        Returns MeshData depending of shape_type of area light.
        Possible values of shape_type: 'SQUARE', 'RECTANGLE', 'DISK', 'ELLIPSE'
        """

        bm = bmesh.new()
        try:
            if shape_type in ('SQUARE', 'RECTANGLE'):
                bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)

            elif shape_type in ('DISK', 'ELLIPSE'):
                bmesh.ops.create_circle(bm, cap_ends=True, cap_tris=True, segments=segments, radius=0.5)

            elif shape_type == 'SPHERE':
                bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=segments, diameter=1.0)

            elif shape_type == 'CUBE':
                bmesh.ops.create_cube(bm, size=size)

            else:
                raise TypeError("Incorrect shape type", shape_type)

            data = MeshData()

            # getting uvs before modifying mesh
            bm.verts.ensure_lookup_table()
            main_uv_set = np.fromiter(
                (vert.co[i] + 0.5 for vert in bm.verts for i in (0, 1)),
                dtype=np.float32).reshape(-1, 2)
            data.uvs = [main_uv_set]

            # scale and rotate mesh around Y axis
            bmesh.ops.scale(bm, verts=bm.verts,
                            vec=(size, size if shape_type in ('SQUARE', 'DISK', 'SPHERE') else size_y, size))
            bmesh.ops.rotate(bm, verts=bm.verts,
                             matrix=mathutils.Matrix.Rotation(math.pi, 4, 'Y'))

            # preparing mesh to get data
            bm.verts.ensure_lookup_table()
            bm.faces.ensure_lookup_table()
            loop_triangles = bm.calc_loop_triangles()
            tris_len = len(loop_triangles)

            data.vertices = np.fromiter(
                (x for vert in bm.verts for x in vert.co),
                dtype=np.float32).reshape(-1, 3)
            data.normals = np.fromiter(
                (x for vert in bm.verts for x in vert.normal),
                dtype=np.float32).reshape(-1, 3)

            data.num_face_vertices = np.full((tris_len,), 3, dtype=np.int32)
            data.vertex_indices = np.fromiter((vert.vert.index for tri in loop_triangles for vert in tri), dtype=np.int32)
            data.normal_indices = data.vertex_indices
            data.uv_indices = [data.vertex_indices]

            data.area = sum(face.calc_area() for face in bm.faces)

            return data

        finally:
            bm.free()


def sync_visibility(rpr_context, obj: bpy.types.Object, rpr_shape, indirect_only: bool = False):
    from hdusd.engine.viewport_engine import ViewportEngine

    rpr_shape.set_visibility(
        obj.show_instancer_for_viewport if rpr_context.engine_type == ViewportEngine.TYPE else
        obj.show_instancer_for_render
    )
    if not rpr_shape.is_visible:
        return

    obj.rpr.export_visibility(rpr_shape, indirect_only)
    obj.rpr.export_subdivision(rpr_shape)

    if obj.rpr.portal_light:
        # Register mesh as a portal light, set "Environment" light group
        rpr_shape.set_light_group_id(0)
        rpr_shape.set_portal_light(True)
    else:
        # all non-portal light meshes are set to light group 3 for emissive objects
        rpr_shape.set_light_group_id(3)
        rpr_shape.set_portal_light(False)


def sync(obj_prim, obj: bpy.types.Object, mesh: bpy.types.Mesh = None, **kwargs):
    """ Creates pyrpr.Shape from obj.data:bpy.types.Mesh """
    from .object import sdf_name

    if not mesh:
        mesh = obj.data

    log("sync", mesh, obj)
    
    data = MeshData.init_from_mesh(mesh, obj=obj)
    if not data:
        return

    stage = obj_prim.GetStage()

    usd_mesh = UsdGeom.Mesh.Define(stage, obj_prim.GetPath().AppendChild(Tf.MakeValidIdentifier(mesh.name)))
        
    usd_mesh.CreateDoubleSidedAttr(True)
    usd_mesh.CreateFaceVertexIndicesAttr(data.vertex_indices)
    usd_mesh.CreateFaceVertexCountsAttr(data.num_face_vertices)

    usd_mesh.CreateSubdivisionSchemeAttr(UsdGeom.Tokens.none)
    usd_mesh.SetNormalsInterpolation(UsdGeom.Tokens.faceVarying)

    points_attr = usd_mesh.CreatePointsAttr(data.vertices)
    normals_attr = usd_mesh.CreateNormalsAttr(data.normals)
    
    # here we can't just call mesh.calc_loop_triangles to update loops because Blender crashes
    armature = obj.find_armature()
    if armature and kwargs.get('is_use_animation', False):
        scene = kwargs.get('scene')
        
        frame_current = scene.frame_current

        frame_start = kwargs.get('frame_start') if kwargs.get('is_restrict_frames') else scene.frame_start
        frame_end = kwargs.get('frame_end') if kwargs.get('is_restrict_frames') else scene.frame_end

        for frame in range(frame_start, frame_end + 1):
            scene.frame_set(frame)
            new_mesh = obj.to_mesh()

            new_data = MeshData.init_from_mesh(new_mesh, obj=obj)

            points_attr.Set(new_data.vertices, frame)
            normals_attr.Set(new_data.normals, frame)

        obj.to_mesh_clear()
    
        scene.frame_set(frame_current)

    for name, uv_layer in data.uv_layers.items():
        uv_primvar = UsdGeom.PrimvarsAPI(usd_mesh.GetPrim()).CreatePrimvar("st",   # default name, later we'll use sdf_path(name)
                                            Sdf.ValueTypeNames.TexCoord2fArray,
                                            UsdGeom.Tokens.faceVarying)
        uv_primvar.Set(uv_layer[0])
        uv_primvar.SetIndices(Vt.IntArray.FromNumpy(uv_layer[1]))

        break   # currently we use only first UV layer

    _assign_materials(obj_prim, obj.original, usd_mesh)


def _assign_materials(obj_prim, obj, usd_mesh):
    usd_mat = None
    if obj.material_slots and obj.material_slots[0].material:
        usd_mat = material.sync(obj_prim, obj.material_slots[0].material, obj)

    if usd_mat:
        UsdShade.MaterialBindingAPI(usd_mesh).Bind(usd_mat)


def sync_update(obj_prim, obj: bpy.types.Object, mesh: bpy.types.Mesh = None, **kwargs):
    """ Update existing mesh from obj.data: bpy.types.Mesh or create a new mesh """
    if not mesh:
        mesh = obj.data

    log("sync_update", mesh, obj)

    stage = obj_prim.GetStage()
    for child_prim in obj_prim.GetAllChildren():
        stage.RemovePrim(child_prim.GetPath())

    sync(obj_prim, obj, **kwargs)
