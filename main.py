import tkinter as tk
import sys

from window_ui import MainUI
from communication import check_connect, stop_get_sensor_info, stop_get_touch_info

root = tk.Tk()
program = MainUI(root)
root.mainloop()

if check_connect == (1,):
    program.stop_draw_text.set()
    program.stop_draw_touch.set()

sys.exit()