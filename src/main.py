from typing import Dict, Union

from open3d.visualization import gui, rendering

from components import Button, Gui
from constants import DEFAULT_LIGHT_POSITION
from src.light import Light, Sun, PointLight


class SMPLPlayground:
    def __init__(self):
        gui.Application.instance.initialize()

        self._window = gui.Application.instance.create_window("SMPL Playground", 1400, 1000)
        self._window.set_on_key(self._on_key_event)
        self._window.set_on_layout(self._on_layout)

        self._scene_widget = gui.SceneWidget()
        self._scene_widget.scene = rendering.Open3DScene(self._window.renderer)
        self._scene_widget.scene.set_background([0.0, 0.0, 0.0, 1.0])
        self._window.add_child(self._scene_widget)

        self.scene = self._scene_widget.scene.scene

        self._lights: Dict[str, Light] = {}
        self._current_light: Union[Light, None] = None

        self._sun = Sun(self.scene)

        self._build_gui()

        gui.Application.instance.post_to_main_thread(self._window, lambda: self._on_layout(None))


    def run(self):
        try:
            gui.Application.instance.run()
        except Exception as e:
            print(f"An error occurred while running the application: {e}")
        finally:
            self._print_params_info()

    def _on_key_event(self, event: gui.KeyEvent) -> bool:
        ...

    def _on_layout(self, context):
        content_rect = self._window.content_rect
        panel_width = min(340, int(content_rect.width * 0.3))
        self._scroll.frame = gui.Rect(content_rect.x, content_rect.y, panel_width, content_rect.height)
        self._scene_widget.frame = gui.Rect(content_rect.x + panel_width, content_rect.y, max(0, content_rect.width - panel_width), content_rect.height)

    def _refresh_layout(self):
        gui.Application.instance.post_to_main_thread(self._window, lambda: self._window.set_needs_layout())

    def _build_gui(self):
        self._panel = gui.Vert(0, gui.Margins(4, 4, 4, 4))
        self._scroll = gui.ScrollableVert()
        self._scroll.add_child(self._panel)
        self._window.add_child(self._scroll)

        # Lights/SMPL panel
        self._lights_panel = gui.Vert(4, gui.Margins(0, 0, 0, 0))
        self._panel.add_child(self._lights_panel)

        self._smpl_panel = gui.Vert(4, gui.Margins(0, 0, 0, 0))
        self._smpl_panel.visible = False

        # Light/SMPL toggle buttons
        menu_row = gui.Horiz(2, gui.Margins(2, 2, 2, 2))
        self._lights_button = Button("Lights", self._show_lights_menu, enabled=False)
        menu_row.add_child(self._lights_button)
        self._smpl_button = Button("SMPL", self._show_smpl_menu)
        menu_row.add_child(self._smpl_button)
        self._lights_panel.add_child(menu_row)

        self._build_lights_menu()
        self._build_smpl_menu()

    def _build_lights_menu(self):
        self._lights_panel.visible = True

        self._lights_panel.add_child(Button("Add point light", lambda e: self._add_point_light()))
        self._lights_panel.add_child(Button("Add spot light", lambda e: self._add_spot_light()))

        self._sun.build_gui(self._panel)

    def _build_smpl_menu(self):
        ...

    def _show_lights_menu(self, e):
        e.enabled = False
        self._smpl_button.enabled = True

        self._lights_panel.visible = True
        self._smpl_panel.visible = False
        self._refresh_layout()

    def _show_smpl_menu(self, e):
        e.enabled = False
        self._lights_button.enabled = True

        self._lights_panel.visible = False
        self._smpl_panel.visible = True
        self._refresh_layout()

    def _add_point_light(self):
        light = PointLight(self.scene, position=DEFAULT_LIGHT_POSITION)
        light.build_gui(self._lights_panel)

        self._lights[light.name] = light
        #self._select_light(light)  TODO: implement selection
        #self._refresh_light_combobox(light)  TODO: implement light combobox

    def _add_spot_light(self):
        ...


    def _print_params_info(self):
        ...

if __name__ == "__main__":
    app = SMPLPlayground()
    app.run()
