import time
import random
import re
import tkinter as tk

from preset_var import sensor_info

class CliDevice():
    def __init__(self):
        self.raw_readings = [random.randint(850,950) for _ in range(34)]
        self.global_sense_adjusts = 1
        self.sense_adjusts = [0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return

    def write(self, command):
        self.command = command
        time.sleep(0.5)
        self.handler()

    def readlines(self):
        return self.handler()

    def handler(self):
        if self.command == b'?\n': return self.help()
        elif self.command == b'raw\n': return self.raw()
        elif self.command == b'display\n': return self.display()
        elif self.command.startswith(b'sense'): return self.sense(self.command[5:].decode())

    def help(self):
        response = ['\t<<Mai Pico Controller>>\r\n','https://...\r\n','\tSN: SimulatingDevice1234\r\n','Built: November 7, 2024\n','Available commands:...\r\n']
        return [i.encode() for i in response]

    def raw(self):
        response = ['Touch raw readings:\r\n',
                    '   |__1__|__2__|__3__|__4__|__5__|__6__|__7__|__8__|\r\n',
                    ' A | '+re.sub("[\\[\\]]","", str(self.raw_readings[0:8])).replace(',',' |')+' |\r\n',
                    ' B | '+re.sub("[\\[\\]]","", str(self.raw_readings[8:16])).replace(',',' |')+' |\r\n',
                    ' C | '+re.sub("[\\[\\]]","", str(self.raw_readings[16:18])).replace(',',' |')+' |\r\n',
                    ' D | '+re.sub("[\\[\\]]","", str(self.raw_readings[18:26])).replace(',',' |')+' |\r\n',
                    ' E | '+re.sub("[\\[\\]]","", str(self.raw_readings[26:34])).replace(',',' |')+' |\r\n',]
        return [i.encode() for i in response]

    def display(self):
        response = ['[RGB]\r\n',
                    '  Number per button: 1, number per aux: 1\r\n',
                    '  Key on: c0c0c0, off: 080808\r\n',
                    '  Level: 127\r\n',
                    '[Sense]\r\n',
                    '  Filter: 0, 1, 0\r\n',
                    f'  Sensitivity (global: {self.global_sense_adjusts:+}):\r\n',
                    '     |_1_|_2_|_3_|_4_|_5_|_6_|_7_|_8_|\r\n',
                    '   A | '+re.sub("[\\[\\]]", "",str(self.sense_adjusts[0:8])).replace(',',' |')+' |\r\n',
                    '   B | '+re.sub("[\\[\\]]", "",str(self.sense_adjusts[8:16])).replace(',',' |')+' |\r\n',
                    '   C | '+re.sub("[\\[\\]]", "",str(self.sense_adjusts[16:18])).replace(',',' |')+' |\r\n',
                    '   D | '+re.sub("[\\[\\]]", "",str(self.sense_adjusts[18:26])).replace(',',' |')+' |\r\n',
                    '   E | '+re.sub("[\\[\\]]", "",str(self.sense_adjusts[26:34])).replace(',',' |')+' |\r\n',
                    '  Debounce (touch, release): 1, 2\r\n',
                    '[HID]\r\n',
                    '  Joy: off, NKRO: key1\r\n',
                    'mai_pico>']
        return [i.encode() for i in response]

    def sense(self, cmd):
        arg = cmd.split()
        if len(arg) == 1:
            if arg[0] == "+":   self.global_sense_adjusts += 1
            elif arg[0] == "-": self.global_sense_adjusts -= 1
            elif arg[0] == "0": self.global_sense_adjusts = 0
        elif len(arg) == 2:
            if arg[1] == "+":   self.sense_adjusts[sensor_info.index(arg[0])] += 1
            elif arg[1] == "-": self.sense_adjusts[sensor_info.index(arg[0])] -= 1
            elif arg[1] == "0": self.sense_adjusts[sensor_info.index(arg[0])] = 0
        print(f"[Cli device] Global {self.global_sense_adjusts:+}\n  {self.sense_adjusts}")
        response = ['Save requested.\r\n']
        return [i.encode() for i in response]

class TouchDevice:
    def __init__(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return

    def write(self, command):
        self.command = command

    def readlines(self):
        if   self.command == b'{RSET}': return b'(RSET)'
        elif self.command == b'{HALT}': return b'(HALT)'
        elif self.command.startswith(b'{L'): return self.command.decode().replace('{', '(').replace('}', ')').encode()
        elif self.command == b'{STAT}': return self.status()

    def read(self):
        return self.status()

    def close(self):
        return

    def status(self):
        # self.controller = tk.Tk()
        # self.active_stat = [tk.IntVar() for _ in range(34)]
        # self.active_box = [tk.Checkbutton(self.controller, variable=self.active_stat[i], command=lambda: print([i.get() for i in self.active_stat])) for i in range(34)]
        # for i in range(0,16):
            # self.active_box[i].grid(row=i//8,column=i%8)
        # for i in range(16,18):
            # self.active_box[i].grid(row=i//8,column=i%8)
        # for i in range(18,34):
            # self.active_box[i].grid(row=(i+6)//8,column=(i+6)%8)
            #
        # self.controller.mainloop()
        pass


if __name__ == "__main__":
    cli = CliDevice()
    touch = TouchDevice()
    cli.display()