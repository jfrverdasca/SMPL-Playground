from typing import Literal, Union

from open3d.cpu.pybind.visualization import gui, rendering

from constants import DEFAULT_LIGHT_POSITION
from gui.components import Separator
from light import PointLight, SpotLight, Sun
from model import Model


class LightControls:

    SELECTED_LIGHT_MARKER_COLOR = (1.0, 0.0, 0.0)

    def __init__(
        self,
        scene: rendering.Scene,
        parent: gui.Widget,
        refresh_layout_callback: callable,
    ):
        self._scene = scene
        self._parent = parent
        self._refresh_layout_callback = refresh_layout_callback

        self._lights = {}
        self._current_light = None

        # Components
        self._point_light_button = gui.Button("Add point light")
        self._point_light_button.set_on_clicked(lambda: self._add_light("PointLight"))

        self._spot_light_button = gui.Button("Add spot light")
        self._spot_light_button.set_on_clicked(lambda: self._add_light("SpotLight"))

        self._lights_combobox = gui.Combobox()
        self._lights_combobox.set_on_selection_changed(self._on_selected_light_change)
        self._lights_combobox.enabled = False

        self._remove_light_button = gui.Button("Remove light")
        self._remove_light_button.set_on_clicked(self._on_remove_light_click)
        self._remove_light_button.enabled = False

        self._parent.add_child(self._point_light_button)
        self._parent.add_child(self._spot_light_button)
        self._parent.add_child(Separator())
        self._parent.add_child(self._lights_combobox)
        self._parent.add_child(self._remove_light_button)
        self._parent.add_child(Separator())

        self._sun = Sun(self._scene)
        self._parent.add_child(self._sun.build_gui())

        self._parent.add_child(Separator())

        self._current_light_options_panel = gui.Vert(4, gui.Margins(0, 0, 0, 0))
        self._parent.add_child(self._current_light_options_panel)

        self._refresh_layout()

    @property
    def combobox(self):
        return self._lights_combobox

    @property
    def point_light_button(self):
        return self._point_light_button

    @property
    def spot_light_button(self):
        return self._spot_light_button

    @property
    def remove_light_button(self):
        return self._remove_light_button

    @property
    def sun(self):
        return self._sun

    def _add_light(self, type_: Literal["PointLight", "SpotLight"] = "PointLight"):
        if type_ == "SpotLight":
            light = SpotLight(self._scene, position=DEFAULT_LIGHT_POSITION)

        else:
            light = PointLight(self._scene, position=DEFAULT_LIGHT_POSITION)

        self._current_light_options_panel.add_child(light.build_gui())

        self._lights[light.name] = light
        self._select_light(light.name)
        self._refresh_light_combobox(light.name)

        self._lights_combobox.enabled = True
        self._remove_light_button.enabled = True

    def _on_selected_light_change(self, text, idx):
        if text in self._lights:
            self._select_light(text)

    def _on_remove_light_click(self):
        if not self._current_light:
            return

        self._current_light.destroy_gui()
        del self._lights[self._current_light.name]

        # Select first available light
        light_name = list(self._lights.keys())[0] if self._lights else None
        if light_name:
            self._select_light(light_name)

        else:
            self._remove_light_button.enabled = False
            self._lights_combobox.enabled = False

        self._refresh_light_combobox(light_name)
        self._refresh_layout()

    def _refresh_light_combobox(self, selected_light_name: Union[str, None]):
        self._lights_combobox.clear_items()
        for i, (name, light) in enumerate(self._lights.items()):
            self._lights_combobox.add_item(name)
            if name == selected_light_name:
                self._lights_combobox.selected_index = i

    def _select_light(self, name: str):
        if not name or name not in self._lights:
            self._current_light = None
            self._refresh_light_combobox(None)
            return

        if self._current_light:
            if name == self._current_light.name:
                return

            self._current_light.destroy_gui()

            # Selected light may not exist anymore
            if self._current_light.name in self._lights:
                self._current_light.marker.set_color(self._current_light.color)

        self._current_light = self._lights[name]
        self._current_light.marker.set_color(self.SELECTED_LIGHT_MARKER_COLOR)

        if not self._current_light.is_gui_built:
            self._current_light_options_panel.add_child(self._current_light.build_gui())

        self._refresh_layout()

    def _refresh_layout(self):
        if self._refresh_layout_callback:
            self._refresh_layout_callback()


class SMPLControls:
    def __init__(
        self,
        scene: rendering.Scene,
        parent: gui.Widget,
        refresh_layout_callback: callable,
        *args,
        **kwargs,
    ):
        self._scene = scene
        self._parent = parent
        self._refresh_layout_callback = refresh_layout_callback

        self._model = Model(scene, *args, **kwargs)

    @property
    def model(self):
        return self._model

    def _refresh_layout(self):
        if self._refresh_layout_callback:
            self._refresh_layout_callback()
