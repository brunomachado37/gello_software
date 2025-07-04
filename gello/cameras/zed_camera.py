import os
import cv2
import time
from typing import List, Optional, Tuple

import pyzed.sl as sl
import numpy as np

from gello.cameras.camera import CameraDriver


def get_devices() -> List[sl.DeviceProperties]:
    cameras = sl.Camera.get_device_list()
    
    return [camera.serial_number for camera in cameras]


class ZedCamera(CameraDriver):
    def __repr__(self) -> str:
        return f"ZedCamera(device_id={self._device_id})"

    def __init__(self, device_id, flip: bool = False):
        self._device_id = device_id

        self._cam = sl.Camera()

        init_params = sl.InitParameters()
        init_params.camera_resolution = sl.RESOLUTION.HD720
        init_params.camera_fps = 30
        init_params.set_from_serial_number(device_id)

        err = self._cam.open(init_params)

        if err != sl.ERROR_CODE.SUCCESS:
            print("Camera Open : "+repr(err)+". Exit program.")

        self._flip = flip

    def read(
        self,
        img_size: Optional[Tuple[int, int]] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Read a frame from the camera.

        Args:
            img_size: The size of the image to return. If None, the original size is returned.

        Returns:
            np.ndarray: The color image, shape=(H, W, 3)
            np.ndarray: The depth image, shape=(H, W, 1)
        """
        left_mat, depth_mat = sl.Mat(), sl.Mat()
        runtime_parameters = sl.RuntimeParameters()
        err = self._cam.grab(runtime_parameters) 

        if err == sl.ERROR_CODE.SUCCESS:
            self._cam.retrieve_image(left_mat, sl.VIEW.LEFT)
            self._cam.retrieve_measure(depth_mat, sl.MEASURE.DEPTH)
            color_image = left_mat.get_data()
            depth_image = depth_mat.get_data()
        else:
            print(f"Error during capture of camera {self._device_id} : {err}")
            return

        if img_size is None:
            image = color_image
            depth = depth_image
        else:
            image = cv2.resize(color_image, img_size)
            depth = cv2.resize(depth_image, img_size)

        if self._flip:
            image = cv2.rotate(image, cv2.ROTATE_180)
            depth = cv2.rotate(depth, cv2.ROTATE_180)[:, :, None]
        else:
            depth = depth[:, :, None]

        return image[:, :, :3][:, :, ::-1], depth
