import os
import time
from tkinter import messagebox
from communication import program_update
from preset_var import message_box_prompts

def main(instance):
    messagebox.showwarning(*message_box_prompts["Update_firmware"])
    instance.stop_draw_touch = 1
    time.sleep(0.1)
    program_update()
    os._exit(0)