from abc import ABCMeta, abstractmethod

from open3d.cpu.pybind.visualization import gui


class GuiComponentInterface(metaclass=ABCMeta):

    def __init__(self):
        self._is_gui_built = False

    @property
    def is_gui_built(self):
        return self._is_gui_built

    @abstractmethod
    def build_gui(self) -> gui.Widget:
        self._is_gui_built = True

    @abstractmethod
    def destroy_gui(self):
        self._is_gui_built = False
