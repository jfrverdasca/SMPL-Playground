import inspect
import math
from typing import Any

import numpy as np


def sphere_dir(azimuth_deg, elevation_deg):
    az = math.radians(azimuth_deg)
    el = math.radians(elevation_deg)
    dx = math.cos(el) * math.sin(az)
    dy = math.sin(el)
    dz = math.cos(el) * math.cos(az)
    return np.array([dx, dy, dz], dtype=np.float32)


def direction_to_yaw_pitch(direction):
    x, y, z = direction
    yaw = math.degrees(math.atan2(x, z))  # azimuth
    hyp = math.sqrt(x * x + z * z)
    pitch = math.degrees(math.atan2(y, hyp))
    return yaw, pitch


def yaw_pitch_to_direction(yaw_degree, pitch_degree):
    yaw = math.radians(yaw_degree)
    pitch = math.radians(pitch_degree)
    dy = math.sin(pitch)
    cp = math.cos(pitch)
    dx = cp * math.sin(yaw)
    dz = cp * math.cos(yaw)
    return np.array([dx, dy, dz], dtype=np.float32)


def get_args_parameter_index(obj: Any, parameter_name: str) -> int:
    signature = inspect.signature(obj)
    parameters = list(signature.parameters.keys())
    if parameter_name in parameters:
        return parameters.index(parameter_name)
    return -1
