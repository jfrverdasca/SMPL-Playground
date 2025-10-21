from typing import Literal, Union

from open3d.cpu.pybind.visualization import gui, rendering

from components.gui import Separator
from components.scene import LightMarker, PointLight, SpotLight, SunLight
from constants import DEFAULT_LIGHT_POSITION


class LightsController:

    SELECTED_LIGHT_MARKER_RADIUS = 0.03
    LIGHT_MOVE_STEP = 0.01

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
        self._point_light_button = gui.Button("Add point light (A)")
        self._point_light_button.set_on_clicked(lambda: self._add_light("PointLight"))

        self._spot_light_button = gui.Button("Add spot light (S)")
        self._spot_light_button.set_on_clicked(lambda: self._add_light("SpotLight"))

        self._lights_combobox = gui.Combobox()
        self._lights_combobox.set_on_selection_changed(self._on_selected_light_change)
        self._lights_combobox.enabled = False

        self._remove_light_button = gui.Button("Remove light (D)")
        self._remove_light_button.set_on_clicked(self._remove_current_light)
        self._remove_light_button.enabled = False

        self._parent.add_child(self._point_light_button)
        self._parent.add_child(self._spot_light_button)
        self._parent.add_child(Separator())
        self._parent.add_child(gui.Label("Selected light:"))
        self._parent.add_child(self._lights_combobox)
        self._parent.add_child(self._remove_light_button)
        self._parent.add_child(Separator())

        sun_controls_collapsable = gui.CollapsableVert("Sun light")
        sun_controls_collapsable.set_is_open(True)

        self._sun = SunLight(self._scene)
        sun_controls_collapsable.add_child(self._sun.build_gui())
        self._parent.add_child(sun_controls_collapsable)

        self._parent.add_child(Separator())

        self._current_light_options_panel = gui.CollapsableVert("Light controls")
        self._current_light_options_panel.visible = False
        self._current_light_options_panel.set_is_open(False)
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
        self._current_light_options_panel.visible = True
        self._current_light_options_panel.set_is_open(True)

    def _on_selected_light_change(self, text, idx):
        if text in self._lights:
            self._select_light(text)

    def _remove_current_light(self):
        if not self._current_light:
            return

        self._current_light.destroy()
        del self._lights[self._current_light.name]

        # Select first available light
        light_name = list(self._lights.keys())[0] if self._lights else None
        if light_name:
            self._select_light(light_name)

        else:
            self._remove_light_button.enabled = False
            self._lights_combobox.enabled = False
            self._current_light_options_panel.visible = False
            self._current_light_options_panel.set_is_open(False)

        self._refresh_light_combobox(light_name)
        self._refresh_layout()

    def on_key_event_handler(self, event: gui.KeyEvent) -> bool:
        if event.type != gui.KeyEvent.DOWN:
            return False

        key = getattr(event, "key", None)
        if key is None:
            return False

        light_move_keys = {263, 264, 265, 266, 270, 271}
        if key in light_move_keys:
            self._move_current_light(key)
            return True
        if key in (ord("a"), ord("A")):
            self._add_light("PointLight")
            return True
        if key in (ord("s"), ord("S")):
            self._add_light("SpotLight")
            return True
        if key in (ord("d"), ord("D")):
            self._remove_current_light()
            return True
        if key in (ord("z"), ord("Z")):
            # TODO: select previous light
            return True
        if key in (ord("x"), ord("X")):
            # TODO: select previous light
            return True

        return False

    def _move_current_light(self, key: int):
        if not self._current_light:
            return

        position = self._current_light.position
        if key == 265:  # up
            position[1] += self.LIGHT_MOVE_STEP
        elif key == 263:  # left
            position[0] -= self.LIGHT_MOVE_STEP
        elif key == 266:  # down
            position[1] -= self.LIGHT_MOVE_STEP
        elif key == 264:  # right
            position[0] += self.LIGHT_MOVE_STEP
        elif key == 271:  # page up
            position[2] += self.LIGHT_MOVE_STEP
        elif key == 270:  # page down
            position[2] -= self.LIGHT_MOVE_STEP

        self._current_light.set_position(position)

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
                self._current_light.marker.set_radius(LightMarker.DEFAULT_RADIUS)

        self._current_light = self._lights[name]
        self._current_light.marker.set_radius(self.SELECTED_LIGHT_MARKER_RADIUS)

        if not self._current_light.is_gui_built:
            self._current_light_options_panel.add_child(self._current_light.build_gui())

        self._refresh_layout()

    def _refresh_layout(self):
        if self._refresh_layout_callback:
            self._refresh_layout_callback()
