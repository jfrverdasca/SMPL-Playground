from open3d.visualization import gui


class Separator(gui.Label):

    def __init__(self):
        super().__init__("")
        self.height_em = 0.5
        self.horizontal_padding_em = 0
        self.vertical_padding_em = 1


class ErrorDialog:

    def __init__(self, window: gui.Window, title: str, message: str):
        self._window = window
        self._dialog = gui.Dialog(title)

        content = gui.Vert(8, gui.Margins(8, 8, 8, 8))
        content.add_child(gui.Label(message))

        row = gui.Horiz(2, gui.Margins(0, 0, 0, 0))
        ok_button = gui.Button("OK")
        ok_button.set_on_clicked(lambda: window.close_dialog())
        row.add_child(ok_button)

        content.add_child(row)
        self._dialog.add_child(content)

    def show(self):
        self._window.show_dialog(self._dialog)
