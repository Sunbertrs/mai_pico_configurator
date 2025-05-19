from tkinter import *
from tkinter.ttk import *

from communication import get_brightness_level, adjust_brightness_level

def main(instance):
    def change_level_number(value):
        level_stat['text'] = str(int(float(value)))

    def close_window():
        window.destroy()
        instance.done_command("esc")

    def apply_and_exit():
        if get_brightness_level() != level_stat['text']:
            adjust_brightness_level(level_stat['text'])
        close_window()
        instance.done_command("refresh")

    window = Toplevel()
    window.title("LED brightness")
    window.resizable(False, False)
    window.protocol("WM_DELETE_WINDOW", close_window)

    Label(window, text="Adjust your button brightness.").grid(padx=15, pady=15, row=0, columnspan=2, sticky="W")

    level_slider = Scale(window, from_=0, to=255, length=300, value=0, command=change_level_number)
    level_slider.grid(padx=15, pady=20, row=1, columnspan=2)

    level_stat = Label(window, text="0", width=3)
    level_stat.grid(padx=15, pady=15, row=1, column=2, sticky="W")

    Button(window, text="Apply", command=lambda: adjust_brightness_level(level_stat['text'])).grid(padx=15, pady=20, row=3, sticky="W")

    Button(window, text="OK", command=apply_and_exit).grid(row=3, column=1, sticky="W")

    level_slider['value'] = int(get_brightness_level())
    level_stat['text'] = get_brightness_level()
