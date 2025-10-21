from open3d.cpu.pybind.visualization import gui, rendering

from components.scene import Model


class ModelController:
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
