from tkinter import *
from tkinter import messagebox
from tkinter.ttk import *

from preset_var import setting_port_manually_text, message_box_prompts

class ManualSelectUI:
    def __init__(self, root: Toplevel):
        self.root = root
        self.root.title(setting_port_manually_text[0])
        self.root.geometry("400x250")
        root.resizable(False, False)

        self.hint = Label(self.root, text=setting_port_manually_text[1])
        self.hint.grid(row=0, column=0, columnspan=2, padx=15, pady=15, sticky="W")

        self.select_list = [
            [Label(self.root, text=setting_port_manually_text[2]), Combobox(self.root)],
            [Label(self.root, text=setting_port_manually_text[3]), Combobox(self.root)]
        ]

        self.select_list[0][1]['values'] = self.select_list[1][1]['values'] = [f'COM{i+1}' for i in range(255)] if os.name == 'nt' else [i for i in glob.glob('/dev/tty*')]
        for i, widget in enumerate(self.select_list):
            widget[0].grid(row=i+1,column=0, padx=15, pady=15, sticky='W')
            widget[1].grid(row=i+1, column=1)

        Button(self.root, text='OK', command=self.validate_config).grid(row=3, padx=15, pady=10)

    def validate_config(self):
        _cli_port = self.select_list[0][1].get()
        _touch_port = self.select_list[1][1].get()
        if _cli_port == _touch_port:
            messagebox.showwarning(*message_box_prompts["Manual_port_repeat"])
            self.root.destroy()
            return
        elif _cli_port == '' or _touch_port == '':
            messagebox.showwarning(*message_box_prompts["Manual_port_empty"])
            self.root.destroy()
            return
        elif not _cli_port.startswith(("COM", "/dev/")) or not _touch_port.startswith(("COM", "/dev/")):
            messagebox.showwarning(*message_box_prompts["Manual_port_illegal"])
            self.root.destroy()
            return
        self.write_config()

    def write_config(self):
        with open('config.yaml', 'r') as f:
            config_content = f.readlines()
            config_content[5] = f"cli_port: '{self.select_list[0][1].get()}'\n"
            config_content[6] = f"touch_port: '{self.select_list[1][1].get()}'\n"
        with open('../config.yaml', 'w+') as f:
            f.writelines(config_content)

        if check_connect() != (1,):
            messagebox.showerror(*message_box_prompts["Manual_port_fail"])
            self.root.destroy()