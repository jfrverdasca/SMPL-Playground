import uuid
from abc import ABCMeta, abstractmethod
from typing import Tuple, Union

import numpy as np
import open3d as o3d
from open3d.cpu.pybind.visualization import rendering
from open3d.visualization import gui

from gui.components import GuiComponentInterface, Separator
from utils import sphere_dir, yaw_pitch_to_direction


class LightMarker:

    def __init__(
        self,
        scene: rendering.Scene,
        name: str,
        position: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        color: Tuple[float, float, float] = (1.0, 1.0, 1.0),
        radius: float = 0.01,
    ):
        self._scene = scene
        self._name = name
        self._position = position
        self._color = color
        self._radius = radius

        self._sphere = None
        self._material = None

        self._update()

    def set_scene(self, scene: rendering.Scene):
        self._scene = scene
        self._update()

    def set_position(self, position: Tuple[float, float, float]):
        self._position = position
        self._update()

    def set_color(self, color: Union[Tuple[float, float, float], gui.Color]):
        if isinstance(color, gui.Color):
            color = (color.red, color.green, color.blue)

        self._color = color
        self._update()

    def set_radius(self, radius: float):
        self._radius = radius
        self._update()

    def _update(self):
        self._sphere = o3d.geometry.TriangleMesh.create_sphere(radius=self._radius)
        self._sphere.compute_vertex_normals()
        self._sphere.translate(self._position)
        self._sphere.paint_uniform_color(self._color)

        if not self._material:
            self._material = rendering.MaterialRecord()
            self._material.shader = "defaultUnlit"
        self._material.base_color = (*self._color, 1.0)

        if self._scene.has_geometry(self._name):
            self._scene.remove_geometry(self._name)
        self._scene.add_geometry(self._name, self._sphere, self._material)

    def destroy(self):
        if self._scene.has_geometry(self._name):
            self._scene.remove_geometry(self._name)
        self._material = None


class Light(metaclass=ABCMeta):

    MAX_INTENSITY = 200000.0

    def __init__(
        self,
        scene: rendering.Scene,
        name: str = None,
        color: Tuple[float, float, float] = (1.0, 1.0, 1.0),
        intensity: float = 100000.0,
    ):
        self._scene = scene
        self._name = name if name else f"l_{uuid.uuid4().hex[:6]}"
        self._color = color
        self._intensity = intensity

        self._marker = LightMarker(self._scene, f"m_{self._name}", color=self._color)

        self._update()

    @abstractmethod
    def destroy(self):
        pass

    @abstractmethod
    def _update(self):
        pass

    @property
    def name(self) -> str:
        return self._name

    @property
    def color(self) -> Tuple[float, float, float]:
        return self._color

    @property
    def marker(self) -> LightMarker:
        return self._marker

    def set_scene(self, scene: rendering.Scene):
        self._scene = scene
        self._marker.set_scene(self._scene)
        self._update()

    def set_color(self, color: Union[Tuple[float, float, float], gui.Color]):
        if isinstance(color, gui.Color):
            color = (color.red, color.green, color.blue)

        self._color = color
        self._marker.set_color(self._color)
        self._update()

    def set_intensity(self, intensity: float):
        self._intensity = intensity
        self._update()


class Sun(Light, GuiComponentInterface):

    MAX_AZIMUTH_DEG = 360
    MAX_ELEVATION_DEG = 360

    def __init__(
        self,
        scene: rendering.Scene,
        azimuth_deg: float = 240.0,
        elevation_deg: float = 10.0,
        color: Tuple[float, float, float] = (1.0, 1.0, 1.0),
        intensity: float = 100000.0,
        enabled: bool = True,
        indirect_light_enable: bool = True,
    ):
        self._azimuth_deg = azimuth_deg
        self._elevation_deg = elevation_deg
        self._enabled = enabled
        self._indirect_light_enable = indirect_light_enable

        # Before calling super we need to set spotlight specific attributes due to _update call
        super().__init__(scene, "Sun", color, intensity)

        # gui
        self._controls_group = gui.Vert(4, gui.Margins(0, 0, 0, 0))

    def set_azimuth(self, azimuth_deg: float):
        self._azimuth_deg = azimuth_deg
        self._update()

    def set_elevation(self, elevation_deg: float):
        self._elevation_deg = elevation_deg
        self._update()

    def set_enabled(self, enabled: bool):
        self._enabled = enabled
        self._update()

    def set_indirect_light_enabled(self, indirect_light_enabled: bool):
        self._indirect_light_enable = indirect_light_enabled
        self._scene.enable_indirect_light(indirect_light_enabled)

    def build_gui(self):
        self._controls_group.add_child(gui.Label("Sun light settings"))
        self._controls_group.add_child(Separator())

        self._controls_group.add_child(gui.Label("Azimuth"))
        azimuth_slider = gui.Slider(gui.Slider.DOUBLE)
        azimuth_slider.set_limits(0.0, self.MAX_AZIMUTH_DEG)
        azimuth_slider.double_value = self._azimuth_deg
        azimuth_slider.set_on_value_changed(self.set_azimuth)
        self._controls_group.add_child(azimuth_slider)

        self._controls_group.add_child(gui.Label("Elevation"))
        elevation_slider = gui.Slider(gui.Slider.DOUBLE)
        elevation_slider.set_limits(0.0, self.MAX_ELEVATION_DEG)
        elevation_slider.double_value = self._elevation_deg
        elevation_slider.set_on_value_changed(self.set_elevation)
        self._controls_group.add_child(elevation_slider)

        self._controls_group.add_child(gui.Label("Intensity"))
        intensity_slider = gui.Slider(gui.Slider.DOUBLE)
        intensity_slider.set_limits(0.0, self.MAX_INTENSITY)
        intensity_slider.double_value = self._intensity
        intensity_slider.set_on_value_changed(self.set_intensity)
        self._controls_group.add_child(intensity_slider)

        self._controls_group.add_child(gui.Label("Color"))
        color_edit = gui.ColorEdit()
        color_edit.color_value = gui.Color(*self._color, 1.0)
        color_edit.set_on_value_changed(self.set_color)
        self._controls_group.add_child(color_edit)

        enable_checkbox = gui.Checkbox("Enabled")
        enable_checkbox.checked = self._enabled
        enable_checkbox.set_on_checked(self.set_enabled)
        self._controls_group.add_child(enable_checkbox)

        enable_checkbox = gui.Checkbox("Indirect light enabled")
        enable_checkbox.checked = self._indirect_light_enable
        enable_checkbox.set_on_checked(self.set_indirect_light_enabled)
        self._controls_group.add_child(enable_checkbox)

        return self._controls_group

    def destroy_gui(self):
        if not self._controls_group:
            return

        for child in self._controls_group.children:
            child.visible = False
        self._controls_group = None

    def destroy(self):
        raise NotImplemented("Sun light cannot be destroyed. Try disabling it instead.")

    def _update(self):
        direction = sphere_dir(self._azimuth_deg, self._elevation_deg)
        self._scene.set_sun_light(direction, self._color, self._intensity)
        self._scene.enable_sun_light(self._enabled)


class PointLight(Light, GuiComponentInterface):

    MAX_FALLOFF = 1000.0

    def __init__(
        self,
        scene: rendering.Scene,
        name: str = None,
        position: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        color: Tuple[float, float, float] = (1.0, 1.0, 1.0),
        intensity: float = 100000.0,
        falloff: float = 1000.0,
        cast_shadow: bool = True,
    ):
        self._position = np.array(position, dtype=np.float32)
        self._falloff = falloff
        self._cast_shadow = cast_shadow

        if not name:
            name = f"pl_{uuid.uuid4().hex[:6]}"

        # Before calling super we need to set spotlight specific attributes due to _update call
        super().__init__(scene, name, color, intensity)

        # gui
        self._controls_group = gui.Vert(4, gui.Margins(0, 0, 0, 0))

    def set_position(self, position: Tuple[float, float, float]):
        self._position = position
        self._marker.set_position(self._position)
        self._update()

    def set_falloff(self, falloff: float):
        self._falloff = falloff
        self._update()

    def set_cast_shadow(self, cast_shadow: bool):
        self._cast_shadow = cast_shadow
        self._update()

    def build_gui(self):
        self._controls_group.add_child(gui.Label("Point light settings"))
        self._controls_group.add_child(Separator())

        self._controls_group.add_child(gui.Label("Intensity"))
        intensity_slider = gui.Slider(gui.Slider.DOUBLE)
        intensity_slider.set_limits(0.0, self.MAX_INTENSITY)
        intensity_slider.double_value = self._intensity
        intensity_slider.set_on_value_changed(self.set_intensity)
        self._controls_group.add_child(intensity_slider)

        self._controls_group.add_child(gui.Label("Falloff"))
        falloff_slider = gui.Slider(gui.Slider.DOUBLE)
        falloff_slider.set_limits(0.0, self.MAX_FALLOFF)
        falloff_slider.double_value = self._falloff
        falloff_slider.set_on_value_changed(self.set_falloff)
        self._controls_group.add_child(falloff_slider)

        self._controls_group.add_child(gui.Label("Color"))
        color_edit = gui.ColorEdit()
        color_edit.color_value = gui.Color(*self._color, 1.0)
        color_edit.set_on_value_changed(self.set_color)
        self._controls_group.add_child(color_edit)

        cast_shadows_checkbox = gui.Checkbox("Cast shadows")
        cast_shadows_checkbox.checked = self._cast_shadow
        cast_shadows_checkbox.set_on_checked(self.set_cast_shadow)
        self._controls_group.add_child(cast_shadows_checkbox)

        return self._controls_group

    def destroy_gui(self):
        super().destroy_gui()

    def destroy(self):
        super().destroy()
        self.destroy_gui()

    def _update(self):
        self._scene.remove_light(self._name)
        self._scene.add_point_light(
            self._name,
            self._color,
            self._position,
            self._intensity,
            self._falloff,
            self._cast_shadow,
        )


class SpotLight(PointLight):

    MIN_YAW = -180.0
    MAX_YAW = 180.0
    MIN_PITCH = -90.0
    MAX_PITCH = 90.0
    MAX_CONE_ANGLE = 1.0

    def __init__(
        self,
        scene: rendering.Scene,
        name: str = None,
        position: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        yaw: float = 0.0,
        pitch: float = 0.0,
        color: Tuple[float, float, float] = (1.0, 1.0, 1.0),
        intensity: float = 100000.0,
        falloff: float = 1000.0,
        cast_shadow: bool = True,
        inner_cone_angle: float = 1.0,
        outer_cone_angle: float = 1.0,
    ):
        self._yaw = yaw
        self._pitch = pitch
        self._inner_cone_angle = inner_cone_angle
        self._outer_cone_angle = outer_cone_angle

        if not name:
            name = f"sl_{uuid.uuid4().hex[:6]}"

        # Before calling super we need to set spotlight specific attributes due to _update call
        super().__init__(scene, name, position, color, intensity, falloff, cast_shadow)

    def set_yaw(self, yaw: float):
        self._yaw = yaw
        self._update()

    def set_pitch(self, pitch: float):
        self._pitch = pitch
        self._update()

    def set_inner_cone_angle(self, angle: float):
        self._inner_cone_angle = angle
        self._update()

    def set_outer_cone_angle(self, angle: float):
        self._outer_cone_angle = angle
        self._update()

    def build_gui(self):
        self._controls_group.add_child(super().build_gui())

        self._controls_group.add_child(gui.Label("Yaw"))
        yaw_slider = gui.Slider(gui.Slider.DOUBLE)
        yaw_slider.set_limits(self.MIN_YAW, self.MAX_YAW)
        yaw_slider.double_value = self._yaw
        yaw_slider.set_on_value_changed(self.set_yaw)
        self._controls_group.add_child(yaw_slider)

        self._controls_group.add_child(gui.Label("Pitch"))
        pitch_slider = gui.Slider(gui.Slider.DOUBLE)
        pitch_slider.set_limits(self.MIN_PITCH, self.MAX_PITCH)
        pitch_slider.double_value = self._pitch
        pitch_slider.set_on_value_changed(self.set_pitch)
        self._controls_group.add_child(pitch_slider)

        self._controls_group.add_child(gui.Label("Inner Cone Angle"))
        inner_cone_angle_slider = gui.Slider(gui.Slider.DOUBLE)
        inner_cone_angle_slider.set_limits(0.0, self.MAX_CONE_ANGLE)
        inner_cone_angle_slider.double_value = self._inner_cone_angle
        inner_cone_angle_slider.set_on_value_changed(self.set_inner_cone_angle)
        self._controls_group.add_child(inner_cone_angle_slider)

        self._controls_group.add_child(gui.Label("Outer Cone Angle"))
        outer_cone_angle_slider = gui.Slider(gui.Slider.DOUBLE)
        outer_cone_angle_slider.set_limits(0.0, self.MAX_CONE_ANGLE)
        outer_cone_angle_slider.double_value = self._outer_cone_angle
        outer_cone_angle_slider.set_on_value_changed(self.set_outer_cone_angle)
        self._controls_group.add_child(outer_cone_angle_slider)

        return self._controls_group

    def _update(self):
        direction = yaw_pitch_to_direction(self._yaw, self._pitch)

        self._scene.remove_light(self._name)
        self._scene.add_spot_light(
            self._name,
            self._color,
            self._position,
            direction,
            self._intensity,
            self._falloff,
            self._inner_cone_angle,
            self._outer_cone_angle,
            self._cast_shadow,
        )
