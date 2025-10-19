import uuid
from abc import ABCMeta, abstractmethod
from typing import Tuple, Union

import open3d as o3d
from open3d.cpu.pybind.visualization import rendering
from open3d.visualization import gui

from gui.components import Checkbox, ColorEdit, GuiComponentInterface, Separator, Slider
from utils import sphere_dir, yaw_pitch_to_direction


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
        self._name = name if name else uuid.uuid4().hex[:6]
        self._color = color
        self._intensity = intensity

    @property
    def name(self) -> str:
        return self._name

    @property
    def color(self) -> Tuple[float, float, float]:
        return self._color

    def set_scene(self, scene: rendering.Scene):
        self._scene = scene
        self._update()

    def set_color(self, color: Union[Tuple[float, float, float], gui.Color]):
        if isinstance(color, gui.Color):
            color = (color.red, color.green, color.blue)

        self._color = color
        self._update()

    def set_intensity(self, intensity: float):
        self._intensity = intensity
        self._update()

    @abstractmethod
    def destroy(self):
        pass

    @abstractmethod
    def _update(self):
        pass


class LightMarker(metaclass=ABCMeta):

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
        self._color = color  # not conflict with Light color
        self._radius = radius

        self._material = None

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
        super().__init__(scene, "Sun", color, intensity)

        self._azimuth_deg = azimuth_deg
        self._elevation_deg = elevation_deg
        self._enabled = enabled
        self._indirect_light_enable = indirect_light_enable

        # gui
        self._controls_group = gui.Vert(4, gui.Margins(0, 0, 0, 0))

        self._update()

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

    def build_gui(self, parent: gui.Widget):
        self._controls_group.add_child(gui.Label("Sun light settings"))
        self._controls_group.add_child(Separator())
        self._controls_group.add_child(gui.Label("Azimuth"))
        self._controls_group.add_child(
            Slider(
                gui.Slider.DOUBLE,
                0.0,
                self.MAX_AZIMUTH_DEG,
                self._azimuth_deg,
                lambda e, v: self.set_azimuth(v),
            )
        )
        self._controls_group.add_child(gui.Label("Elevation"))
        self._controls_group.add_child(
            Slider(
                gui.Slider.DOUBLE,
                0.0,
                self.MAX_ELEVATION_DEG,
                self._elevation_deg,
                lambda e, v: self.set_elevation(v),
            )
        )
        self._controls_group.add_child(gui.Label("Intensity"))
        self._controls_group.add_child(
            Slider(
                gui.Slider.DOUBLE,
                0.0,
                self.MAX_INTENSITY,
                self._intensity,
                lambda e, v: self.set_intensity(v),
            )
        )
        self._controls_group.add_child(gui.Label("Color"))
        self._controls_group.add_child(
            ColorEdit(self._color, lambda e, v: self.set_color(v))
        )
        self._controls_group.add_child(
            Checkbox("Enabled", self._enabled, lambda e, v: self.set_enabled(v))
        )
        self._controls_group.add_child(
            Checkbox(
                "Indirect light enabled",
                self._indirect_light_enable,
                lambda e, v: self.set_indirect_light_enabled(v),
            )
        )

        parent.add_child(self._controls_group)

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


class PointLight(Light, LightMarker, GuiComponentInterface):

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
        Light.__init__(self, scene, name, color, intensity)
        LightMarker.__init__(self, scene, f"m_{self._name}", position, color)

        self._position = position
        self._falloff = falloff
        self._cast_shadow = cast_shadow

        # gui
        self._controls_group = gui.Vert(4, gui.Margins(0, 0, 0, 0))

        self._update()

    def set_maker_color(self, color: Tuple[float, float, float]):
        LightMarker.set_color(self, color)
        self._update()

    def set_position(self, position: Tuple[float, float, float]):
        self._position = position
        self._update()

    def set_falloff(self, falloff: float):
        self._falloff = falloff
        self._update()

    def set_cast_shadow(self, cast_shadow: bool):
        self._cast_shadow = cast_shadow
        self._update()

    def build_gui(self, parent: gui.Widget):
        self._controls_group.add_child(gui.Label("Point light settings"))
        self._controls_group.add_child(Separator())
        self._controls_group.add_child(gui.Label("Intensity"))
        self._controls_group.add_child(
            Slider(
                gui.Slider.DOUBLE,
                0.0,
                self.MAX_INTENSITY,
                self._intensity,
                lambda v: self.set_intensity(v),
            )
        )
        self._controls_group.add_child(gui.Label("Falloff"))
        self._controls_group.add_child(
            Slider(
                gui.Slider.DOUBLE,
                0.0,
                self.MAX_FALLOFF,
                self._falloff,
                lambda v: self.set_falloff(v),
            )
        )
        self._controls_group.add_child(gui.Label("Color"))
        self._controls_group.add_child(
            ColorEdit(self._color, lambda v: self.set_color(v))
        )
        self._controls_group.add_child(
            Checkbox(
                "Cast shadows", self._cast_shadow, lambda v: self.set_cast_shadow(v)
            )
        )

        parent.add_child(self._controls_group)

    def destroy_gui(self):
        super().destroy_gui()

    def destroy(self):
        super().destroy()
        self.destroy_gui()

    def _update(self):
        LightMarker._update(self)

        self._scene.remove_light(self._name)
        self._scene.add_point_light(
            self._name,
            self._position,
            self._color,
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
        super().__init__(scene, name, position, color, intensity, falloff, cast_shadow)

        self._yaw = yaw
        self._pitch = pitch
        self._inner_cone_angle = inner_cone_angle
        self._outer_cone_angle = outer_cone_angle

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

    def build_gui(self, parent: gui.Widget):
        super().build_gui(parent)
        self._controls_group.add_child(gui.Label("Yaw"))
        self._controls_group.add_child(
            Slider(
                gui.Slider.DOUBLE,
                self.MIN_YAW,
                self.MAX_YAW,
                self._yaw,
                lambda v: self.set_yaw(v),
            )
        )
        self._controls_group.add_child(gui.Label("Pitch"))
        self._controls_group.add_child(
            Slider(
                gui.Slider.DOUBLE,
                self.MIN_PITCH,
                self.MAX_PITCH,
                self._pitch,
                lambda v: self.set_pitch(v),
            )
        )
        self._controls_group.add_child(gui.Label("Inner Cone Angle"))
        self._controls_group.add_child(
            Slider(
                gui.Slider.DOUBLE,
                0.0,
                self.MAX_CONE_ANGLE,
                self._inner_cone_angle,
                lambda v: self.set_inner_cone_angle(v),
            )
        )
        self._controls_group.add_child(gui.Label("Outer Cone Angle"))
        self._controls_group.add_child(
            Slider(
                gui.Slider.DOUBLE,
                0.0,
                self.MAX_CONE_ANGLE,
                self._outer_cone_angle,
                lambda v: self.set_outer_cone_angle(v),
            )
        )

        parent.add_child(self._controls_group)

    def _update(self):
        LightMarker._update(self)

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
