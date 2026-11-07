import os
import subprocess
import sys
import time
from tkinter import messagebox
import yaml
from threading import Thread
from tkinter import *
from PIL import Image, ImageTk

import draw
from gui.gui_manual import ManualSelectUI
from communication import check_connect, create_connection, stop_get_touch_info, init_sensor_touch, \
    get_hardware_basic_info
from preset_var import button_stat, message_box_prompts, get_canvas_size  # connect_stat,

def configuration() -> dict[str, str]:
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    return config

def gui_update_after_connected(gui_inst) -> None:
    gui_inst.root.protocol("WM_DELETE_WINDOW", lambda:after_window_close(gui_inst))
    gui_inst.connect_btn['state'] = DISABLED
    gui_inst.connect_stat_label['text'] = button_stat[2]
    config = configuration()
    for i, j in enumerate((config['cli_port'], config['touch_port'], config['led_port'], config['aime_port']),start=1):
        gui_inst.connected_port_table.set(f"I00{i}", "#2", j)
    for i, j in enumerate(get_hardware_basic_info(), start=1):
        gui_inst.basic_info_table.set(f"I00{i}", "#2", j)
    gui_inst.log_handler.write_inf("Connected to device.")
    # gui_inst.current_stat['text'] = connect_stat[1]
    # gui_inst.basic_info_label['text'] = get_hardware_basic_info()

def after_window_close(gui_inst) -> None:
    gui_inst.stop_draw_text = 1
    gui_inst.log_handler.write_inf("Stopped draw text thread.")
    gui_inst.stop_draw_touch = 1
    gui_inst.log_handler.write_inf("Stopped draw touch thread.")
    stop_get_touch_info()
    gui_inst.log_handler.write_inf("Stopped polling status of the touch port.")
    sys.exit()

def connect_error_messagebox(error_info: str, gui_inst=None) -> None:
    if "PermissionError" in error_info:
        messagebox.showerror(message_box_prompts["Denied"][0], message_box_prompts["Denied"][1]+"\n"+error_info)
    elif "FileNotFoundError" in error_info:
        if configuration()["auto_port_config"]:
            auto_config()
        else:
            manual_config(gui_inst)

def connect_button_clicked(gui_inst) -> None:
    stat = check_connect()
    if stat == (1,):
        create_connection()
        gui_update_after_connected(gui_inst)
        if init_sensor_touch():
            Thread(target=gui_inst.canvas_handler.daemon_draw_text, daemon=True).start()
            Thread(target=gui_inst.canvas_handler.daemon_draw_touch, daemon=True).start()
            for i in gui_inst.cmd_btn: i['state'] = NORMAL
            return
        else:
            messagebox.showerror(*message_box_prompts["Communicate_failed"])
    elif stat[1] == "no_value":
        if configuration()["auto_port_config"]:
            auto_config()
        else:
            manual_config(gui_inst)
    elif stat[0] != 1:
        connect_error_messagebox(stat[1], gui_inst)
        return

def manual_config(gui_inst) -> None:
    if not gui_inst.manual_select_port_is_opened:
        gui_inst.manual_select_port_is_opened = 1
        gui_inst.select_port_window = ManualSelectUI(Toplevel())
    else:
        gui_inst.select_port_window.root.destroy()
        gui_inst.manual_select_port_is_opened = 0
        manual_config(gui_inst)

def auto_config() -> None:
    com_list = get_com_list()
    if com_list == {}:
        messagebox.showerror(*message_box_prompts["Not_detected"])
        return
    elif len(com_list) == 3:
        aime = None
    for k, v in com_list.items():
        if "command" in v.lower():
            cli = k
        elif "touch" in v.lower():
            touch = k
        elif "led" in v.lower():
            led = k
        elif "aime" in v.lower():
            aime = k
    modify_config_file(cli, touch, led, aime)
    messagebox.showinfo(*message_box_prompts["Reconfig"])

def modify_config_file(cli: str, touch: str, led: str, aime: str) -> None:
    with open('config.yaml', 'r') as f:
        config_content = f.readlines()
    for i, line in enumerate(config_content):
        if "cli_port:" in line:
            config_content[i] = f"cli_port: '{cli}'\n"
        elif "touch_port:" in line:
            config_content[i] = f"touch_port: '{touch}'\n"
        elif "led_port:" in line:
            config_content[i] = f"led_port: '{led}'\n"
        elif "aime_port:" in line:
            config_content[i] = f"aime_port: '{aime}'\n"
    with open('config.yaml', 'w') as f:
        f.writelines(config_content)

def get_com_list() -> dict[str, str]:
    if os.name == "nt":
        return get_com_list_windows_method()
    elif sys.platform == "linux" or sys.platform == "darwin":
        pass

def get_com_list_windows_method() -> dict[str, str]:
    subprocess.run(['powershell', """
        try{
            $number = (Get-WMIObject Win32_PnPEntity | Where-Object {$_.PNPClass -eq "Ports" -and $_.Name -match "COM"}).Name
            $name = (Get-WMIObject Win32_PnPEntity | Where-Object {$_.PNPClass -eq "Ports" -and $_.Name -match "COM"}).GetDeviceProperties("DEVPKEY_Device_BusReportedDeviceDesc").deviceProperties.Data
            if (Get-ChildItem | Where-Object Name -eq list) {
                del ./list
            }
        }catch{
            Set-Content -Path ./list -Value ""
            exit
        }
        $i=0
        foreach($num in $number){
            $num = $num -replace "[^com\\d\\d]", ""
            if($exist -eq 1){
                break
            }else{
                [PSCustomObject]@{ Number = $num; Name = $name[$i] } | Export-Csv -NoTypeInformation -Path ./list -Append
                $exist=1
            }
            $i++
            $exist=0
        }
    """])
    with open("list", "r", encoding="utf-8") as f:
        com_list = {}
        content = f.readlines()
    os.remove("list")
    if len(content) == 1:
        return com_list
    for i in content:
        if "Mai Pico" in i:
            tmp = i.replace('"', "").replace(",", ":").strip().split(":")
            com_list[tmp[0]] = tmp[1]
    return com_list

def execute_command(self, name, cmd):
    # self.current_stat['text'] = connect_stat[2] + name + "."
    # self.stop_draw_text = 1
    # for i in ["Left", "Right", "Up", "Down", "Return", "Insert", "End"] + [i for i in range(10)]:
    #     self.root.unbind(f"<KeyPress-{i}>")
    # self.root.bind("<KeyPress-Escape>", lambda _: self.done_command("esc"))
    time.sleep(0.18)
    exec(f"from {cmd} import main as _command_main\nThread(target=_command_main, args=(self,)).start()")

def done_command(self, cmd):
    self.root.unbind("<KeyPress-Escape>")
    self.root.unbind("<KeyPress-Backspace>")
    # self.current_stat['text'] = connect_stat[1]
    if cmd == "esc":
        self.stop_draw_text = 0
    elif cmd == "refresh":
        self.basic_info_label['text'] = get_hardware_basic_info()
        self.stop_draw_text = 0

def disconnected_unexpectedly(gui_inst):
    gui_inst.connect_btn['state'] = NORMAL
    # gui_inst.connect_stat_label['text'] = button_stat[1]
    for i in gui_inst.cmd_btn: i['state'] = DISABLED
    # self.current_stat['text'] = connect_stat[0]
    messagebox.showerror(*message_box_prompts["Disconnected"])


class CanvasHandler:
    def __init__(self, canvas: Canvas):
        self.canvas = canvas
        self.sensor_touch_prev = []
        self.size = get_canvas_size()
        self.stop_draw_text = 0
        self.stop_draw_touch = 0

    def set_text(self, image):
        if self.canvas.find_withtag("text"):
            self.canvas.delete("text")
        self.sensor_text_photoimage = ImageTk.PhotoImage(image)
        self.canvas.create_image(self.size / 2, self.size / 2, image=self.sensor_text_photoimage, tag="text")

    def set_touch(self, image_list: list):
        if len(image_list) == 0:
            self.canvas.delete("touch")
            return
        elif len(self.sensor_touch_prev) != 0 and self.sensor_touch_prev == image_list:
            return
        sensor_touch_stat = Image.new('RGBA', (self.size,) * 2)
        for i in image_list:
            sensor_touch_stat.paste(i, (0, 0), i)
        self.sensor_touch_photoimage = ImageTk.PhotoImage(sensor_touch_stat.resize((self.size,) * 2))
        self.canvas.delete("touch")
        self.canvas.create_image(self.size / 2, self.size / 2, image=self.sensor_touch_photoimage, tag="touch")
        self.canvas.tag_raise("text")
        self.sensor_touch_prev = image_list

    def daemon_draw_text(self):
        config = configuration()["raw_readings_interval_time"]
        if config == 0:
            self.set_text(draw.draw_text())
            self.stop_draw_text = 1
        while True:
            if not self.stop_draw_text:
                tmp = draw.draw_text()
                if not self.stop_draw_text:
                    self.set_text(tmp)
            time.sleep(config)

    def daemon_draw_touch(self):
        while True:
            if not self.stop_draw_touch:
                tmp = draw.draw_touch()
                if tmp == ["Lost"]: break
                self.set_touch(tmp)
        # disconnected_unexpectedly()


class LogHandler:
    def __init__(self, display: Text):
        self.log_display: Text = display

    def _write_log(self, level: str, content: str) -> None:
        self.log_display["state"] = NORMAL
        log = f"[{level}] {content}\n"
        self.log_display.insert(INSERT, log)
        self.log_display["state"] = DISABLED

    def write_inf(self, content: str) -> None:
        self._write_log("INF", content)

    def write_wrn(self, content: str) -> None:
        self._write_log("WRN", content)

    def write_err(self, content: str) -> None:
        self._write_log("ERR", content)

if __name__ == "__main__":
    print(get_com_list())