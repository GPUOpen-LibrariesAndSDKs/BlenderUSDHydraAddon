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

from pxr import UsdGeom, Gf, Tf
import bpy

from ..utils import logging
log = logging.Log('export.camera')


# Core has issues with drawing faces in orthographic camera view with big
# ortho depth (far_clip_plane - near_clip_plane).
# Experimentally found quite suited value = 200
MAX_ORTHO_DEPTH = 200.0


@dataclass(init=False, eq=True)
class CameraData:
    """ Comparable dataclass which holds all camera settings """

    mode: int = None
    clip_plane: (float, float) = None
    focal_length: float = None
    sensor_size: (float, float) = None
    transform: tuple = None
    lens_shift: (float, float) = None
    ortho_size: (float, float) = None
    dof_data: (float, float, int) = None # tuple which holds data in following order: focus_distance, f_stop, blades

    @staticmethod
    def init_from_camera(camera: bpy.types.Camera, transform, ratio, border=((0, 0), (1, 1))):
        """ Returns CameraData from bpy.types.Camera """

        pos, size = border

        data = CameraData()
        data.clip_plane = (camera.clip_start, camera.clip_end)
        data.transform = tuple(transform)
        data.mode = camera.type

        if camera.dof.use_dof:
            # calculating focus_distance
            if not camera.dof.focus_object:
                focus_distance = camera.dof.focus_distance
            else:
                obj_pos = camera.dof.focus_object.matrix_world.to_translation()
                camera_pos = transform.to_translation()
                focus_distance = (obj_pos - camera_pos).length

            data.dof_data = (max(focus_distance, 0.001),
                             camera.dof.aperture_fstop,
                             camera.dof.aperture_blades)
        else:
            data.dof_data = None

        if camera.sensor_fit == 'VERTICAL':
            data.lens_shift = (camera.shift_x / ratio, camera.shift_y)
        elif camera.sensor_fit == 'HORIZONTAL':
            data.lens_shift = (camera.shift_x, camera.shift_y * ratio)
        elif camera.sensor_fit == 'AUTO':
            data.lens_shift = (camera.shift_x, camera.shift_y * ratio) if ratio > 1.0 else \
                (camera.shift_x / ratio, camera.shift_y)
        else:
            raise ValueError("Incorrect camera.sensor_fit value", camera, camera.sensor_fit)

        data.lens_shift = tuple(data.lens_shift[i] / size[i] + (pos[i] + size[i] * 0.5 - 0.5) / size[i] for i in (0, 1))

        if camera.type == 'PERSP':
            data.focal_length = camera.lens
            if camera.sensor_fit == 'VERTICAL':
                data.sensor_size = (camera.sensor_height * ratio, camera.sensor_height)
            elif camera.sensor_fit == 'HORIZONTAL':
                data.sensor_size = (camera.sensor_width, camera.sensor_width / ratio)
            else:
                data.sensor_size = (camera.sensor_width, camera.sensor_width / ratio) if ratio > 1.0 else \
                                   (camera.sensor_width * ratio, camera.sensor_width)

            data.sensor_size = tuple(data.sensor_size[i] * size[i] for i in (0, 1))


        elif camera.type == 'ORTHO':
            if camera.sensor_fit == 'VERTICAL':
                data.ortho_size = (camera.ortho_scale * ratio, camera.ortho_scale)
            elif camera.sensor_fit == 'HORIZONTAL':
                data.ortho_size = (camera.ortho_scale, camera.ortho_scale / ratio)
            else:
                data.ortho_size = (camera.ortho_scale, camera.ortho_scale / ratio) if ratio > 1.0 else \
                                  (camera.ortho_scale * ratio, camera.ortho_scale)

            data.ortho_size = tuple(data.ortho_size[i] * size[i] for i in (0, 1))
            data.clip_plane = (camera.clip_start, min(camera.clip_end, MAX_ORTHO_DEPTH + camera.clip_start))

        elif camera.type == 'PANO':
            # TODO: Recheck parameters for PANO camera
            data.focal_length = camera.lens
            if camera.sensor_fit == 'VERTICAL':
                data.sensor_size = (camera.sensor_height * ratio, camera.sensor_height)
            elif camera.sensor_fit == 'HORIZONTAL':
                data.sensor_size = (camera.sensor_width, camera.sensor_width / ratio)
            else:
                data.sensor_size = (camera.sensor_width, camera.sensor_width / ratio) if ratio > 1.0 else \
                                   (camera.sensor_width * ratio, camera.sensor_width)

            data.sensor_size = tuple(data.sensor_size[i] * size[i] for i in (0, 1))

        else:
            raise ValueError("Incorrect camera.type value",camera, camera.type)

        return data

    @staticmethod
    def init_from_context(context: bpy.types.Context):
        """ Returns CameraData from bpy.types.Context """

        VIEWPORT_SENSOR_SIZE = 72.0     # this constant was found experimentally, didn't find such option in
                                        # context.space_data or context.region_data

        ratio = context.region.width / context.region.height
        if context.region_data.view_perspective == 'PERSP':
            data = CameraData()
            data.mode = 'PERSP'
            data.clip_plane = (context.space_data.clip_start, context.space_data.clip_end)
            data.lens_shift = (0.0, 0.0)
            data.focal_length = context.space_data.lens
            data.sensor_size = (VIEWPORT_SENSOR_SIZE, VIEWPORT_SENSOR_SIZE / ratio) if ratio > 1.0 else \
                               (VIEWPORT_SENSOR_SIZE * ratio, VIEWPORT_SENSOR_SIZE)
            data.transform = tuple(context.region_data.view_matrix.inverted())

        elif context.region_data.view_perspective == 'ORTHO':
            data = CameraData()
            data.mode = 'ORTHO'
            ortho_size = context.region_data.view_distance * VIEWPORT_SENSOR_SIZE / context.space_data.lens
            data.lens_shift = (0.0, 0.0)
            ortho_depth = min(context.space_data.clip_end, MAX_ORTHO_DEPTH)
            data.clip_plane = (-ortho_depth * 0.5, ortho_depth * 0.5)
            data.ortho_size = (ortho_size, ortho_size / ratio) if ratio > 1.0 else \
                              (ortho_size * ratio, ortho_size)

            data.transform = tuple(context.region_data.view_matrix.inverted())

        elif context.region_data.view_perspective == 'CAMERA':
            camera_obj = context.space_data.camera
            data = CameraData.init_from_camera(camera_obj.data, context.region_data.view_matrix.inverted(), ratio)

            # This formula was taken from previous plugin with corresponded comment
            # See blender/intern/cycles/blender/blender_camera.cpp:blender_camera_from_view (look for 1.41421f)
            zoom = 4.0 / (2.0 ** 0.5 + context.region_data.view_camera_zoom / 50.0) ** 2

            # Updating lens_shift due to viewport zoom and view_camera_offset
            # view_camera_offset should be multiplied by 2
            data.lens_shift = ((data.lens_shift[0] + context.region_data.view_camera_offset[0] * 2) / zoom,
                               (data.lens_shift[1] + context.region_data.view_camera_offset[1] * 2) / zoom)

            if data.mode == 'ORTHO':
                data.ortho_size = (data.ortho_size[0] * zoom, data.ortho_size[1] * zoom)
            else:
                data.sensor_size = (data.sensor_size[0] * zoom, data.sensor_size[1] * zoom)

        else:
            raise ValueError("Incorrect view_perspective value", context.region_data.view_perspective)

        return data

    @staticmethod
    def init_from_usd_camera(prim):
        data = CameraData()

        stage = prim.GetStage()
        xform_camera = stage.DefinePrim(prim.GetPath().pathString, prim.GetTypeName())
        usd_camera = UsdGeom.Camera.Get(stage, prim.GetPath())

        data.transform = UsdGeom.XformCache(bpy.context.scene.frame_current).GetLocalToWorldTransform(xform_camera)

        data.mode = usd_camera.GetProjectionAttr().Get()
        data.focal_length = usd_camera.GetFocalLengthAttr().Get()

        aperture = (usd_camera.GetHorizontalApertureAttr().Get(), usd_camera.GetVerticalApertureAttr().Get())
        if data.mode == 'perspective':
            data.sensor_size = aperture

        elif data.mode == 'orthographic':
            # Use tenths of a world unit accorging to USD docs https://graphics.pixar.com/usd/docs/api/class_gf_camera.html
            data.ortho_size = tuple(i / 10 for i in aperture)

        return data

    def export(self, usd_camera, tile=((0.0, 0.0), (1.0, 1.0))):
        tile_pos, tile_size = tile

        # usd_camera.set_mode(self.mode)
        usd_camera.CreateClippingRangeAttr(self.clip_plane)

        # following formula is used:
        # lens_shift = lens_shift * resolution / tile_size + (center - resolution/2) / tile_size
        # where: center = tile_pos + tile_size/2
        lens_shift = tuple((self.lens_shift[i] + tile_pos[i] + tile_size[i] * 0.5 - 0.5) / tile_size[i] for i in (0, 1))

        if self.mode == 'PERSP':
            usd_camera.CreateProjectionAttr(UsdGeom.Tokens.perspective)
            usd_camera.CreateFocalLengthAttr(self.focal_length)

            # Why is it only correct with world units when tenths should be used instead according to USD docs?
            sensor_size = tuple(self.sensor_size[i] * tile_size[i] for i in (0, 1))

            usd_camera.CreateHorizontalApertureAttr(sensor_size[0])
            usd_camera.CreateVerticalApertureAttr(sensor_size[1])

            usd_camera.CreateHorizontalApertureOffsetAttr(lens_shift[0] * sensor_size[0])
            usd_camera.CreateVerticalApertureOffsetAttr(lens_shift[1] * sensor_size[1])

        elif self.mode == 'ORTHO':
            usd_camera.CreateProjectionAttr(UsdGeom.Tokens.orthographic)

            # Use tenths of a world unit accorging to USD docs https://graphics.pixar.com/usd/docs/api/class_gf_camera.html
            ortho_size = tuple(self.ortho_size[i] * tile_size[i] * 10 for i in (0, 1))

            usd_camera.CreateHorizontalApertureAttr(ortho_size[0])
            usd_camera.CreateVerticalApertureAttr(ortho_size[1])

            usd_camera.CreateHorizontalApertureOffsetAttr(lens_shift[0] * self.ortho_size[0] * tile_size[0] * 10)
            usd_camera.CreateVerticalApertureOffsetAttr(lens_shift[1] * self.ortho_size[1] * tile_size[1] * 10)

        elif self.mode == 'PANO':
            # TODO: Make panoramic camera
            pass
            # usd_camera.set_sensor_size(*self.sensor_size)
            # usd_camera.set_focal_length(self.focal_length)

        # TODO apply Depth Of Field settings to camera
        if self.dof_data:
            pass
            # usd_camera.set_focus_distance(self.dof_data[0])
            # usd_camera.set_f_stop(self.dof_data[1])
            # usd_camera.set_aperture_blades(self.dof_data[2])
        else:
            pass
            # usd_camera.set_f_stop(None)

        # usd_camera.set_transform(np.array(self.transform, dtype=np.float32))

    def export_gf(self, tile=((0.0, 0.0), (1.0, 1.0))):
        tile_pos, tile_size = tile

        gf_camera = Gf.Camera()
        gf_camera.clippingRange = Gf.Range1f(*self.clip_plane)

        # following formula is used:
        # lens_shift = lens_shift * resolution / tile_size + (center - resolution/2) / tile_size
        # where: center = tile_pos + tile_size/2
        lens_shift = tuple((self.lens_shift[i] + tile_pos[i] + tile_size[i] * 0.5 - 0.5) / tile_size[i] for i in (0, 1))

        if self.mode == 'PERSP':
            gf_camera.projection = Gf.Camera.Perspective
            gf_camera.focalLength = self.focal_length

            sensor_size = tuple(self.sensor_size[i] * tile_size[i] for i in (0, 1))

            gf_camera.horizontalAperture = sensor_size[0]
            gf_camera.verticalAperture = sensor_size[1]

            gf_camera.horizontalApertureOffset = lens_shift[0] * sensor_size[0]
            gf_camera.verticalApertureOffset = lens_shift[1] * sensor_size[1]

        elif self.mode == 'ORTHO':
            gf_camera.projection = Gf.Camera.Orthographic

            # Use tenths of a world unit accorging to USD docs https://graphics.pixar.com/usd/docs/api/class_gf_camera.html
            ortho_size = tuple(self.ortho_size[i] * tile_size[i] * 10 for i in (0, 1))
            log(f"export_gf ortho_size: {ortho_size}")

            gf_camera.horizontalAperture = ortho_size[0]
            gf_camera.verticalAperture = ortho_size[1]

            gf_camera.horizontalApertureOffset = lens_shift[0] * self.ortho_size[0] * tile_size[0] * 10
            gf_camera.verticalApertureOffset = lens_shift[1] * self.ortho_size[1] * tile_size[1] * 10

        elif self.mode == 'PANO':
            # TODO: store panoramic camera settings
            pass
            # usd_camera.set_sensor_size(*self.sensor_size)
            # usd_camera.set_focal_length(self.focal_length)

        if self.dof_data:
            # TODO: store Depth Of Field camera settings
            pass
            # usd_camera.set_focus_distance(self.dof_data[0])
            # usd_camera.set_f_stop(self.dof_data[1])
            # usd_camera.set_aperture_blades(self.dof_data[2])
        else:
            pass
            # usd_camera.set_f_stop(None)

        gf_camera.transform = Gf.Matrix4d(np.transpose(self.transform))

        return gf_camera

    def export_to_camera(self, camera: bpy.types.Object):
        camera.matrix_world = self.transform
        camera_data = camera.data
        if self.mode == 'orthographic':
            camera_data.type = 'ORTHO'
            ratio = self.ortho_size[0]/self.ortho_size[1]
            camera_data.ortho_scale = max(self.ortho_size)
        else:
            camera_data.type = 'PERSP'
            ratio = self.sensor_size[0]/self.sensor_size[1]
            camera_data.lens = self.focal_length

        camera_data.sensor_fit = 'HORIZONTAL' if ratio > 1 else 'VERTICAL'


def sync(obj_prim, obj: bpy.types.Object, **kwargs):
    """Creates Usd camera from obj.data: bpy.types.Camera"""
    scene = kwargs['scene']
    screen_ratio = scene.render.resolution_x / scene.render.resolution_y

    camera = obj.data
    log("sync", camera)

    stage = obj_prim.GetStage()
    usd_camera = UsdGeom.Camera.Define(stage, obj_prim.GetPath().AppendChild(Tf.MakeValidIdentifier(camera.name)))

    settings = CameraData.init_from_camera(camera, obj.matrix_world, screen_ratio)
    settings.export(usd_camera)


def sync_update(obj_prim, obj: bpy.types.Object, **kwargs):
    """ Update existing camera from obj.data: bpy.types.Camera or create a new light """
    camera = obj.data
    log("sync_update", camera, obj)

    stage = obj_prim.GetStage()
    for child_prim in obj_prim.GetAllChildren():
        stage.RemovePrim(child_prim.GetPath())

    sync(obj_prim, obj, **kwargs)
