from open3d.cpu.pybind.visualization import gui

from gui.components import Button, Combobox, Separator


class LightsPanel(gui.Vert):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Callbacks
        self._on_point_light_click = lambda e: True
        self._on_spot_light_click = lambda e: True
        self._on_selected_light_change = lambda e, t, i: True
        self._on_remove_light_click = lambda e: True

        # Components
        self._point_light = Button("Add point light", self._on_point_light_click)
        self._spot_light = Button("Add spot light", self._on_spot_light_click)
        self._combobox = Combobox(self._on_selected_light_change, enabled=False)
        self._remove_light_button = Button(
            "Remove selected light", self._on_remove_light_click, enabled=False
        )

        self.add_child(self._point_light)
        self.add_child(self._spot_light)
        self.add_child(Separator())
        self.add_child(self._combobox)
        self.add_child(self._remove_light_button)
        self.add_child(Separator())

    @property
    def combobox(self):
        return self._combobox

    @property
    def point_light_button(self):
        return self._point_light

    @property
    def spot_light_button(self):
        return self._spot_light

    @property
    def remove_light_button(self):
        return self._remove_light_button

    def on_point_light_changed(self, callback: callable):
        self._on_point_light_click = callback

    def on_spot_light_changed(self, callback: callable):
        self._on_spot_light_click = callback

    def on_selected_light_changed(self, callback: callable):
        self._on_selected_light_change = callback

    def on_remove_light_clicked(self, callback: callable):
        self._on_remove_light_click = callback


class SMPLPanel(gui.Vert):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
