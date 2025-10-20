from abc import ABCMeta, abstractmethod

from open3d.visualization import gui


class GuiComponentInterface(metaclass=ABCMeta):

    @abstractmethod
    def build_gui(self) -> gui.Widget:
        pass

    @abstractmethod
    def destroy_gui(self):
        pass


class Separator(gui.Label):
    def __init__(self):
        super().__init__("")
        self.height_em = 0.5
        self.horizontal_padding_em = 0
        self.vertical_padding_em = 1
