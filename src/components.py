from abc import abstractmethod, ABCMeta

from open3d.visualization import gui


class Gui(metaclass=ABCMeta):

    @abstractmethod
    def build_gui(self, parent: gui.Widget):
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


class Button(gui.Button):
    def __init__(self, text: str, on_click: callable, visible: bool = True, enabled: bool = True):
        super().__init__(text)

        self.set_on_clicked(lambda: on_click(self))
        self.visible = visible
        self.enabled = enabled

        self.horizontal_padding_em = 2


class Checkbox(gui.Checkbox):
    def __init__(self, text: str, is_checked: bool, on_check: callable, visible: bool = True, enabled: bool = True):
        super().__init__(text)

        self.checked = is_checked
        self.set_on_checked(on_check)
        self.visible = visible
        self.enabled = enabled

        self.horizontal_padding_em = 2


class Slider(gui.Slider):
    def __init__(self, slider_type: int, min_value: float, max_value: float, initial_value: float, on_value_changed: callable, visible: bool = True, enabled: bool = True):
        super().__init__(slider_type)

        self.set_limits(min_value, max_value)
        self.set_on_value_changed(on_value_changed)
        self.visible = visible
        self.enabled = enabled

        if slider_type == gui.Slider.INT:
            self.int_value = int(initial_value)
        else:
            self.double_value = float(initial_value)

        self.horizontal_padding_em = 2


class ColorEdit(gui.ColorEdit):
    def __init__(self, initial_color: tuple, on_value_changed: callable, visible: bool = True, enabled: bool = True):
        super().__init__()

        self.color = initial_color
        self.set_on_value_changed(on_value_changed)
        self.visible = visible
        self.enabled = enabled

        self.horizontal_padding_em = 2