import numpy as np
import open3d as o3d
from open3d.cpu.pybind.visualization import gui, rendering
from smplx import SMPL
from sympy.printing.pytorch import torch

from gui.components import GuiComponentInterface


class Model(GuiComponentInterface):

    DEFAULT_SMPL_COLOR = (0.85, 0.82, 0.80)
    DEFAULT_SMPL_POSE = [
        0.000,  # 0 - z
        0.000,  # 1 - y
        0.000,  # 2 - x
        0.000,  # 3 - leg left front/back
        0.000,  # 4 - leg left rotation
        0.000,  # 5 - leg left left/right
        0.000,  # 6 - leg right front/back
        0.000,  # 7 - leg right rotation
        0.000,  # 8 - leg right left/right
        0.000,  # 9 - waist (above belly button) front/back
        0.000,  # 10 - waist (above belly button) rotation
        0.000,  # 11 - waist (above belly button) left/right
        0.000,  # 12 - knee left front/back
        0.000,  # 13 - knee left rotation
        0.000,  # 14 - knee left left/right
        0.000,  # 15 - knee right front/back
        0.000,  # 16 - knee right rotation
        0.000,  # 17 - knee right left/right
        0.000,  # 18 - chest front/back   ?
        0.000,  # 19 - chest rotation     ?
        0.000,  # 20 - chest left/right   ?
        0.000,  # 21 - feet left front/back
        0.300,  # 22 - feet left rotation
        0.000,  # 23 - feet left left/right
        0.000,  # 24 - feet right front/back
        -0.300,  # 25 - feet right rotation
        0.000,  # 26 - feet right left/right
        0.000,  # 27 - chest front/back   ?
        0.000,  # 28 - chest rotation     ?
        0.000,  # 29 - chest left/right   ?
        0.000,  # 30 - feet left toes front/back
        0.000,  # 31 - feet left toes rotation
        0.000,  # 32 - feet left toes left/right
        0.000,  # 33 - feet right toes front/back
        0.000,  # 34 - feet right toes rotation
        0.000,  # 35 - feet right toes left/right
        0.000,  # 36 - neck front/back
        0.000,  # 37 - neck rotation
        0.000,  # 38 - neck left/right
        -0.200,  # 39 - shoulder left toes front/back
        0.000,  # 40 - shoulder left toes rotation
        -0.200,  # 41 - shoulder left toes left/right
        -0.200,  # 42 - shoulder right toes front/back
        0.000,  # 43 - shoulder right toes rotation
        0.200,  # 44 - shoulder right toes left/right
        0.000,  # 45 - head front/back
        0.000,  # 46 - head rotation
        0.000,  # 47 - head left/right
        0.000,  # 48 - arm left rotation
        -0.100,  # 49 - arm left front/back
        -0.800,  # 50 - arm left left/right
        0.000,  # 51 - arm right rotation
        0.100,  # 52 - arm right front/back
        0.800,  # 53 - arm right left/right
        0.400,  # 54 - forearm left rotation
        -0.300,  # 55 - forearm left front/back
        0.000,  # 56 - forearm left left/right
        0.400,  # 57 - forearm right rotation
        0.300,  # 58 - forearm right front/back
        0.000,  # 59 - forearm right left/right
        -0.400,  # 60 - wrist left rotation
        0.000,  # 61 - wrist left front/back
        0.000,  # 62 - wrist left left/right
        -0.400,  # 63 - wrist right rotation
        0.000,  # 64 - wrist right front/back
        0.000,  # 65 - wrist right left/right
        0.000,  # 66 - fingers left rotation
        0.000,  # 67 - fingers left front/back
        -0.300,  # 68 - fingers left left/right
        0.000,  # 69 - fingers right rotation
        0.000,  # 70 - fingers right front/back
        0.300,  # 71 - fingers right left/right
    ]

    def __init__(self, scene: rendering.Scene, *args, **kwargs):
        self._scene = scene

        self._model = SMPL(*args, **kwargs)
        self._pose = torch.tensor(
            self.DEFAULT_SMPL_POSE, dtype=torch.float32
        ).unsqueeze(0)
        self._betas = torch.zeros((1, 10), dtype=torch.float32)
        self._faces = self._model.faces.astype(np.int32)

        self._update()

    @property
    def bounds(self) -> o3d.geometry.AxisAlignedBoundingBox:
        return self._bounds

    @property
    def center(self) -> np.ndarray:
        return self._center

    def destroy_gui(self):
        pass

    def build_gui(self, parent: gui.Widget):
        pass

    def _update(self):
        output = self._model(
            betas=self._betas,
            body_pose=self._pose[:, 3:],
            global_orient=self._pose[:, :3],
        )
        vertices = output.vertices.detach().cpu().numpy().squeeze()

        mesh = o3d.geometry.TriangleMesh()
        mesh.vertices = o3d.utility.Vector3dVector(vertices)
        mesh.triangles = o3d.utility.Vector3iVector(self._faces)
        mesh.compute_vertex_normals()
        mesh.paint_uniform_color(self.DEFAULT_SMPL_COLOR)

        self._bounds = mesh.get_axis_aligned_bounding_box()
        self._center = self._bounds.get_center()

        material = rendering.MaterialRecord()
        material.shader = "defaultLit"
        material.base_color = [*self.DEFAULT_SMPL_COLOR, 1.0]

        self._scene.add_geometry("smpl", mesh, material)
