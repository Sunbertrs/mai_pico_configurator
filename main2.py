import ttkbootstrap as tb

from gui.gui_main2 import MainUI
from preset_var import CONFIG_FILE


def get_theme():
    theme = CONFIG_FILE.get("theme", "")
    if theme == "":
        return "bootstrap-light"
    return theme


def main() -> None:
    app = tb.App(theme=get_theme())
    app.title("mai_pico_configurator")
    app.minsize(660, 900)
    MainUI(app)
    app.mainloop()


if __name__ == "__main__":
    main()