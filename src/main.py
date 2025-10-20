from typing import Dict, Union

from open3d.visualization import gui, rendering

from gui.controls import LightControls, SMPLControls


class SMPLPlayground:
    def __init__(self):
        gui.Application.instance.initialize()

        # Window
        self._window = gui.Application.instance.create_window(
            "SMPL Playground", 1400, 1000
        )
        self._window.set_on_key(self._on_key_event)
        self._window.set_on_layout(self._on_layout)

        # Scene
        self._scene_widget = gui.SceneWidget()
        self._scene_widget.scene = rendering.Open3DScene(self._window.renderer)
        self._scene_widget.scene.set_background([0.0, 0.0, 0.0, 1.0])
        self._window.add_child(self._scene_widget)

        self.scene = self._scene_widget.scene.scene

        # GUI components
        self._build_gui()

        gui.Application.instance.post_to_main_thread(
            self._window, lambda: self._on_layout(None)
        )

    def run(self):
        try:
            gui.Application.instance.run()
        except Exception as e:
            print(f"An error occurred while running the application: {e}")
        finally:
            self._print_params_info()

    def _on_key_event(self, event: gui.KeyEvent) -> bool: ...

    def _on_layout(self, context):
        content_rect = self._window.content_rect
        panel_width = min(340, int(content_rect.width * 0.3))
        self._scroll.frame = gui.Rect(
            content_rect.x, content_rect.y, panel_width, content_rect.height
        )
        self._scene_widget.frame = gui.Rect(
            content_rect.x + panel_width,
            content_rect.y,
            max(0, content_rect.width - panel_width),
            content_rect.height,
        )

    def _refresh_layout(self):
        self._window.set_needs_layout()

        gui.Application.instance.post_to_main_thread(
            self._window, lambda: self._window.set_needs_layout()
        )

    def _build_gui(self):
        # Base panel
        self._panel = gui.Vert(0, gui.Margins(4, 4, 4, 4))
        self._scroll = gui.ScrollableVert()
        self._scroll.add_child(self._panel)
        self._window.add_child(self._scroll)

        # Options panel (Lights/SMPL)
        self._lights_button = gui.Button("Lights")
        self._lights_button.set_on_clicked(self._toggle_lights_smpl_menu)
        self._lights_button.enabled = False

        self._smpl_button = gui.Button("SMPL")
        self._smpl_button.set_on_clicked(self._toggle_lights_smpl_menu)

        self._options_selector_panel = gui.Horiz(2, gui.Margins(4, 4, 4, 4))
        self._options_selector_panel.add_child(self._lights_button)
        self._options_selector_panel.add_child(self._smpl_button)
        self._panel.add_child(self._options_selector_panel)

        # Lights panel
        self._lights_panel = gui.Vert(2, gui.Margins(4, 4, 4, 4))
        self._lights_controls = LightControls(
            self.scene, self._lights_panel, self._refresh_layout
        )
        self._panel.add_child(self._lights_panel)

        # SMPL panel
        self._smpl_panel = gui.Vert(2, gui.Margins(4, 4, 4, 4))
        self._smpl_controls = SMPLControls(
            self.scene,
            self._smpl_panel,
            self._refresh_layout,
            model_path="./smpl",
            model_type="smpl",
        )
        self._panel.add_child(self._smpl_panel)

        self._scene_widget.setup_camera(
            60, self._smpl_controls.model.bounds, self._smpl_controls.model.center
        )

    def _toggle_lights_smpl_menu(self):
        self._lights_button.enabled = not self._lights_button.enabled
        self._smpl_button.enabled = not self._smpl_button.enabled
        self._lights_panel.visible = not self._lights_panel.visible
        self._smpl_panel.visible = not self._smpl_panel.visible

        self._refresh_layout()

    def _print_params_info(self): ...


if __name__ == "__main__":
    app = SMPLPlayground()
    app.run()
