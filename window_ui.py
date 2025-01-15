import sys
from tkinter import *
from tkinter.ttk import *
from tkinter import messagebox

from PIL import Image, ImageTk
import os
from threading import Thread
import time
if os.name != "nt":
    import glob

from preset_var import connect_stat, message_box_prompts, canvas_size, get_com_list, config_file, buttons
from communication import check_connect, create_connection, get_hardware_basic_info, init_sensor_touch, stop_get_touch_info
import draw

class MainUI:
    def __init__(self, root:Tk):
        self.root = root
        self.root.title("Mai_pico Configurator")

        Style().configure("TButton", width=15)

        self.display_area = Frame(root)
        self.display_area.pack(expand=YES, fill=Y)

        self.connect_frame = Frame(self.display_area)
        # ---
        self.connect_frame.grid(row=0, sticky="W", padx=10, pady=10)
        self.connect_btn = Button(self.connect_frame, text="Connect", command=lambda:Thread(target=self.click_start_connect).start())
        self.connect_btn.grid(row=0, column=0, sticky="W")
        self.connect_stat_label = Label(self.connect_frame, text="Disconnected")
        self.connect_stat_label.grid(row=0, column=1, padx=10, sticky="W")
        self.cmd_list = Frame(self.display_area)
        # ---
        self.cmd_list.grid(row=1, pady=15)
        self.cmd_btn = []
        for i, name in enumerate(buttons.keys()):
            self.cmd_btn.append(Button(self.cmd_list, text=name, state=DISABLED, command=lambda current=name: self.execute_command(current, buttons[current])))
            if canvas_size == 1080:
                self.cmd_btn[i].grid(row=i//5, column=i%5, padx=30, pady=10)
            else:
                self.cmd_btn[i].grid(row=i//4, column=i%4, padx=12, pady=10)

        self.basic_info_frame = Frame(self.display_area)
        # ---
        self.basic_info_frame.grid(row=2, sticky="W", padx=10, pady=10)
        self.current_stat = Label(self.basic_info_frame, text=connect_stat[0])
        self.current_stat.grid(row=0, sticky="NW")
        self.basic_info_label = Label(self.basic_info_frame, text="SN: -")
        self.basic_info_label.grid(row=1, pady=10, sticky="NW")
        self.basic_info_frame.grid_rowconfigure(1, minsize=150)

        Separator(self.display_area, orient="horizontal").grid(row=4, sticky="WE")

        self.sensor_frame = Frame(self.display_area)
        # ---
        self.sensor_frame.grid(row=5, sticky="NSEW")
        self.display_area.grid_rowconfigure(5, weight=1)
        self.sensor_canvas = Canvas(self.sensor_frame, width=canvas_size, height=canvas_size) # background='grey'
        self.sensor_canvas.pack(anchor=S, expand=1)
        self.SENSOR_PIC = ImageTk.PhotoImage(Image.open("images/sensor.png").resize((canvas_size,)*2))
        self.sensor_canvas.create_image(canvas_size/2, canvas_size/2, image=self.SENSOR_PIC)

        self.canvas_handler = CanvasHandler(self.sensor_canvas)
        self.stop_draw_text = 0
        self.stop_draw_touch = 0

    def click_start_connect(self):
        stat = check_connect()
        if stat == (1,):
            create_connection()
            self.root.protocol("WM_DELETE_WINDOW", self.exiting)
            self.connect_btn['state'] = DISABLED
            self.connect_stat_label['text'] = "Connected"
            for i in self.cmd_btn: i['state'] = NORMAL
            self.current_stat['text'] = connect_stat[1]
            self.basic_info_label['text'] = get_hardware_basic_info()
            init_sensor_touch()
            Thread(target=self.daemon_draw_text, daemon=True).start()
            Thread(target=self.daemon_draw_touch, daemon=True).start()
            return
        elif len(stat) == 2 and "PermissionError" in str(stat[1]):
            messagebox.showerror(message_box_prompts["Denied"][0], message_box_prompts["Denied"][1]+"\n"+str(stat[1]))
            return
        elif (stat == ('not_set',) or "FileNotFoundError" in str(stat[1])) and os.name == 'nt':
            if config_file["auto_port_config"]:
                self.try_auto_config()
            else:
                self.manual_config()
        else:
            self.manual_config()

        if os.name != "nt":
            self.manual_config()

    def manual_config(self):
        manual_select_window = Tk()
        ManualSelectPort(manual_select_window)
        manual_select_window.mainloop()
        return

    def try_auto_config(self):
        get_com_list()
        com_list = open('com_list.csv').readlines() if os.path.exists('com_list.csv') else 0
        if com_list != 0:
            os.remove('com_list.csv')
            with open('config.yaml', 'r') as f:
                config_content = f.readlines()
            for line in com_list:
                if "Pico" and "Command" in line:
                    line = line[1:6].replace('"', '')
                    config_content[5] = f"cli_port: '{line}'\n"
                elif "Pico" and "Touch" in line:
                    line = line[1:6].replace('"', '')
                    config_content[6] = f"touch_port: '{line}'\n"
            with open('config.yaml', 'w') as f:
                f.writelines(config_content)
            messagebox.showinfo(*message_box_prompts["Reconfig"])
        else:
            messagebox.showerror(*message_box_prompts["Not_detected"])

    def execute_command(self, name, cmd):
        self.current_stat['text'] = connect_stat[2] + name + "."
        self.stop_draw_text = 1
        self.root.bind("<KeyPress-Escape>", lambda _: self.done_command("esc"))
        time.sleep(0.2)
        exec(f"from {cmd} import main as _command_main\nThread(target=_command_main, args=(self,)).start()")

    def done_command(self, cmd):
        self.root.unbind("<KeyPress-Escape>")
        self.current_stat['text'] = connect_stat[1]
        if cmd == "esc":
            self.stop_draw_text = 0
        if cmd == "refresh":
            self.basic_info_label['text'] = get_hardware_basic_info()
            self.stop_draw_text = 0

    def daemon_draw_text(self):
        while True:
            if not self.stop_draw_text:
                self.canvas_handler.set_text(draw.draw_text())
            if config_file["raw_readings_interval_time"] == 0:
                self.stop_draw_text = 1
            time.sleep(config_file["raw_readings_interval_time"])
    
    def daemon_draw_touch(self):
        while True:
            if not self.stop_draw_touch:
                self.canvas_handler.set_touch(draw.draw_touch())

    def exiting(self):
        self.stop_draw_text = 1
        self.stop_draw_touch = 1
        try:
            stop_get_touch_info()
        except Exception:
            pass
        sys.exit()

class CanvasHandler:
    def __init__(self, canvas):
        self.canvas = canvas
        self.sensor_touch_prev = []

    def set_text(self, image):
        if self.canvas.find_withtag("text"):
            self.canvas.delete("text")
        self.sensor_text_photoimage = ImageTk.PhotoImage(image)
        self.canvas.create_image(canvas_size/2, canvas_size/2, image=self.sensor_text_photoimage, tag="text")

    def set_touch(self, imagelist):
        if len(imagelist) == 0:
            self.canvas.delete("touch")
            return
        if len(self.sensor_touch_prev) != 0 and self.sensor_touch_prev == imagelist:
            return
        sensor_touch_stat = Image.new('RGBA', (canvas_size,) * 2)
        for i in imagelist:
            sensor_touch_stat.paste(i, (0, 0), i)
        self.sensor_touch_photoimage = ImageTk.PhotoImage(sensor_touch_stat.resize((canvas_size,) * 2))
        self.canvas.delete("touch")
        self.canvas.create_image(canvas_size/2, canvas_size/2, image=self.sensor_touch_photoimage, tag="touch")
        self.canvas.tag_raise("text")
        self.sensor_touch_prev = imagelist

class ManualSelectPort:
    def __init__(self, root):
        self.root = root
        self.root.title("Setting the COM ports")
        self.root.geometry("380x250")
        root.resizable(False, False)

        self.hint = Label(self.root, text="We can't determine the COM ports.\nPlease specify your ports manually.")
        self.hint.grid(row=0, column=0, columnspan=2, padx=15, pady=15, sticky="W")

        self.select_list = [
            [Label(self.root, text="Command line:"), Combobox(self.root)],
            [Label(self.root, text="Touch:"), Combobox(self.root)]
        ]

        self.select_list[0][1]['values'] = self.select_list[1][1]['values'] = [f'COM{i+1}' for i in range(255)] if os.name == 'nt' else [i for i in glob.glob('/dev/tty*')]
        for i, widget in enumerate(self.select_list):
            widget[0].grid(row=i+1,column=0, padx=15, pady=15, sticky='W')
            widget[1].grid(row=i+1, column=1)

        Button(self.root, text='OK', command=self.validate_config).grid(row=3, pady=10)

    def validate_config(self):
        if self.select_list[0][1].get() == self.select_list[1][1].get():
            messagebox.showwarning(*message_box_prompts["Manual_port_repeat"])
            self.root.destroy()
            return
        elif self.select_list[0][1].get() == '' or self.select_list[1][1].get() == '':
            messagebox.showwarning(*message_box_prompts["Manual_port_empty"])
            self.root.destroy()
            return
        self.write_config()

    def write_config(self):
        with open('config.yaml', 'r') as f:
            config_content = f.readlines()
            config_content[5] = f"cli_port: '{self.select_list[0][1].get()}'\n"
            config_content[6] = f"touch_port: '{self.select_list[1][1].get()}'\n"
        with open('config.yaml', 'w+') as f:
            f.writelines(config_content)

        if check_connect() != (1,):
            messagebox.showerror(*message_box_prompts["Manual_port_fail"])
            self.root.destroy()