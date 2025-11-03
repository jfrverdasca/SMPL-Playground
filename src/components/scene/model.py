from typing import Literal, Tuple, Union

import numpy as np
import open3d as o3d
from open3d.cpu.pybind.visualization import gui, rendering
from smplx import SMPL
from sympy.printing.pytorch import torch

from components import Separator
from components.gui import GuiComponentInterface
from utils import get_args_parameter_index


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
    _GUI_MODEL_PARAMS_GROUPS = [
        "Global orientation",
        "Left leg",
        "Right leg",
        "Waist (Spine)",
        "Knee left",
        "Knee right",
        "Belly (Spine 1)",
        "Ankle left",
        "Ankle right",
        "Chest (Spine 2)",
        "Feet left toes",
        "Feet right toes",
        "Neck",
        "Shoulder left",
        "Shoulder right",
        "Head",
        "Arm left",
        "Arm right",
        "Forearm left",
        "Forearm right",
        "Wrist left",
        "Wrist right",
        "Fingers left",
        "Fingers right",
    ]

    MIN_POSE_VALUE = -3.14
    MAX_POSE_VALUE = 3.14
    MIN_BETAS_VALUE = -5.0
    MAX_BETAS_VALUE = 5.0

    def __init__(self, scene: rendering.Scene, *args, **kwargs):
        super().__init__()

        self._scene = scene
        self._model_args = list(args)  # We need to be able to modify args
        self._model_kwargs = kwargs

        self._name = "smpl"
        self._gender = "neutral"
        self._age = "adult"
        self._color = self.DEFAULT_SMPL_COLOR

        # gui
        self._controls_group = None
        self._pose_controls_group = None  # needed in model reset
        self._betas_controls_group = None  # needed in model reset

        self._reload(full_reload=True)

    @property
    def bounds(self) -> o3d.geometry.AxisAlignedBoundingBox:
        return self._bounds

    @property
    def center(self) -> np.ndarray:
        return self._center

    @property
    def color(self) -> Tuple[float, float, float]:
        return self._color

    def set_color(self, color: Union[Tuple[float, float, float], gui.Color]):
        if isinstance(color, gui.Color):
            color = (color.red, color.green, color.blue)

        self._color = color
        self._update()

    def set_gender(self, gender: Literal["neutral", "male", "female"] = "neutral"):
        self._gender = gender
        self._reload()

    def set_age(self, age: Literal["adult", "kid"] = "adult"):
        self._age = age
        self._reload()

    def build_gui(self) -> gui.Widget:
        super().build_gui()

        self._controls_group = gui.Vert(4, gui.Margins(0, 0, 0, 0))

        reset_model_button = gui.Button("Reset pose and betas")
        reset_model_button.set_on_clicked(self._on_reset_model_click)
        self._controls_group.add_child(reset_model_button)

        # General controls
        general_controls_collapsable = gui.CollapsableVert("General settings")
        general_controls_collapsable.set_is_open(True)

        general_controls_collapsable.add_child(gui.Label("Gender:"))
        gender_radio_button = gui.RadioButton(gui.RadioButton.HORIZ)
        gender_radio_button.set_items(["Neutral", "Male", "Female"])
        gender_radio_button.set_on_selection_changed(
            lambda i: self.set_gender(gender_radio_button.selected_value.lower())
        )
        gender_radio_button.selected_index = 0
        general_controls_collapsable.add_child(gender_radio_button)

        general_controls_collapsable.add_child(gui.Label("Age:"))
        age_radio_button = gui.RadioButton(gui.RadioButton.HORIZ)
        age_radio_button.set_items(["Adult", "Kid"])
        age_radio_button.set_on_selection_changed(
            lambda i: self.set_gender(age_radio_button.selected_value.lower())
        )
        age_radio_button.selected_index = 0
        general_controls_collapsable.add_child(age_radio_button)

        general_controls_collapsable.add_child(gui.Label("Color"))
        color_edit = gui.ColorEdit()
        color_edit.color_value = gui.Color(*self._color, 1.0)
        color_edit.set_on_value_changed(self.set_color)
        general_controls_collapsable.add_child(color_edit)

        self._controls_group.add_child(general_controls_collapsable)
        self._controls_group.add_child(Separator())

        # Pose parameters
        pose_controls_collapsable = gui.CollapsableVert("Pose parameters")
        pose_controls_collapsable.set_is_open(True)

        self._pose_controls_group = gui.Vert(4, gui.Margins(0, 0, 0, 0))
        for i, group_name in enumerate(self._GUI_MODEL_PARAMS_GROUPS):
            self._pose_controls_group.add_child(gui.Label(group_name))

            for j in range(3):
                param_index = i * 3 + j
                pose_slider = gui.Slider(gui.Slider.DOUBLE)
                pose_slider.set_limits(self.MIN_POSE_VALUE, self.MAX_POSE_VALUE)
                pose_slider.double_value = self._pose[0, param_index].item()
                pose_slider.set_on_value_changed(
                    lambda v, p_i=param_index: self._on_pose_param_changed(v, p_i)
                )
                self._pose_controls_group.add_child(pose_slider)

        pose_controls_collapsable.add_child(self._pose_controls_group)
        self._controls_group.add_child(pose_controls_collapsable)
        self._controls_group.add_child(Separator())

        # Betas parameters
        betas_controls_collapsable = gui.CollapsableVert("Shape parameters (Betas)")
        betas_controls_collapsable.set_is_open(True)

        self._betas_controls_group = gui.Vert(4, gui.Margins(0, 0, 0, 0))
        for i in range(10):
            self._betas_controls_group.add_child(gui.Label(f"Beta {i}"))

            beta_slider = gui.Slider(gui.Slider.DOUBLE)
            beta_slider.set_limits(self.MIN_BETAS_VALUE, self.MAX_BETAS_VALUE)
            beta_slider.double_value = self._betas[0, i].item()
            beta_slider.set_on_value_changed(
                lambda v, b_i=i: self._on_betas_param_changed(v, b_i)
            )
            self._betas_controls_group.add_child(beta_slider)

        betas_controls_collapsable.add_child(self._betas_controls_group)
        self._controls_group.add_child(betas_controls_collapsable)

        return self._controls_group

    def destroy_gui(self):
        super().destroy_gui()

        if not self._controls_group:
            return

        for child in self._controls_group.children:
            child.visible = False

        self._pose_controls_group = None
        self._betas_controls_group = None
        self._controls_group = None

    def _on_reset_model_click(self):
        self._reload(full_reload=True)

        # Reset pose sliders
        if self._pose_controls_group:
            i = 0
            for control in self._pose_controls_group.get_children():
                if not isinstance(control, gui.Slider):
                    continue

                control.double_value = self.DEFAULT_SMPL_POSE[i]
                i += 1

        # Reset betas sliders
        if self._betas_controls_group:
            i = 0
            for control in self._betas_controls_group.get_children():
                if not isinstance(control, gui.Slider):
                    continue

                control.double_value = 0.0
                i += 1

    def _on_pose_param_changed(self, value: float, index: int):
        self._pose[0, index] = value
        self._update()

    def _on_betas_param_changed(self, value: float, index: int):
        self._betas[0, index] = value
        self._update()

    def _reload(self, full_reload: bool = False):
        gender_args_index = get_args_parameter_index(SMPL, "gender")
        if 0 < gender_args_index < len(self._model_args):
            self._model_args[gender_args_index] = self._gender
            self._model_kwargs.pop("gender", None)
        else:
            self._model_kwargs["gender"] = self._gender

        age_args_index = get_args_parameter_index(SMPL, "age")
        if 0 < age_args_index < len(self._model_args):
            self._model_args[age_args_index] = self._age
            self._model_kwargs.pop("age", None)
        else:
            self._model_kwargs["age"] = self._age

        self._model = SMPL(*self._model_args, **self._model_kwargs)
        self._faces = self._model.faces.astype(np.int32)

        if full_reload:
            self._pose = torch.tensor(
                self.DEFAULT_SMPL_POSE, dtype=torch.float32
            ).unsqueeze(0)
            self._betas = torch.zeros((1, 10), dtype=torch.float32)

        self._update()

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
        mesh.paint_uniform_color(self._color)

        self._bounds = mesh.get_axis_aligned_bounding_box()
        self._center = self._bounds.get_center()

        material = rendering.MaterialRecord()
        material.shader = "defaultLit"
        material.base_color = [*self._color, 1.0]

        if self._scene.has_geometry(self._name):
            self._scene.remove_geometry(self._name)
        self._scene.add_geometry(self._name, mesh, material)
