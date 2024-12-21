from tkinter import *
from tkinter.ttk import *

from communication import get_brightness_level, adjust_brightness_level

def main(instance):
    def change_level_number(value):
        level_show['text'] = str(int(float(value)))

    def apply_and_exit():
        if get_brightness_level() != level_show['text']:
            adjust_brightness_level(level_show['text'])
        exiting()

    def exiting():
        instance.done_command("refresh")
        window.destroy()

    window = Toplevel()
    window.title("LED brightness")
    window.resizable(False, False)
    window.protocol("WM_DELETE_WINDOW", exiting)

    Label(window, text="Adjust your button brightness.").grid(padx=15, pady=15, row=0, columnspan=2, sticky="W")

    level_slider = Scale(window, from_=0, to=255, length=300, value=int(get_brightness_level()), command=change_level_number)
    level_slider.grid(padx=15, pady=20, row=1, columnspan=2)

    level_show = Label(window, text=get_brightness_level(), width=3)
    level_show.grid(padx=15, pady=15, row=1, column=2, sticky="W")

    Button(window, text="Apply", command=lambda: adjust_brightness_level(level_show['text'])).grid(padx=15, pady=20, row=3, sticky="W")

    Button(window, text="OK", command=apply_and_exit).grid(row=3, column=1, sticky="W")

    window.mainloop()

    instance.done_command("refresh")
