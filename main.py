import tkinter as tk
import sys

from window_ui import MainUI
from communication import check_connect, stop_get_touch_info

root = tk.Tk()
program = MainUI(root)
root.mainloop()

if check_connect == (1,):
    program.stop_draw_text = 1
    program.stop_draw_touch = 1
    stop_get_touch_info()

sys.exit()
