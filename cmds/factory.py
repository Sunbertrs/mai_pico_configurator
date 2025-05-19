from tkinter import messagebox
from communication import factory_reset
from preset_var import message_box_prompts

def main(instance):
    answer = messagebox.askyesno(*message_box_prompts["Factory_warning"])
    if answer:
        factory_reset()
        messagebox.showwarning(*message_box_prompts["Factory_done"])
        instance.done_command("refresh")
    else:
        instance.done_command("esc")