import time
import random
import re

from preset_var import SENSOR_INFO

class CliDevice:
    def __init__(self):
        self.raw_readings = [random.randint(800,1000) for _ in range(34)]
        self.global_sense_adjusts = 1
        self.sense_adjusts = [
            0, 0, 2, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0,
            0, 0,
            0, 0, 0, 0, 0, 0, 0, 0,
            0, 0, 0, 0, 0, 0, 0, 0
        ]
        self.hid_mode = "io4"
        self.aime_module = "PN532"
        self.aime_virtual_aic = "ON"
        self.aime_protocol_mode = "0"

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return

    def write(self, command):
        self.command = command
        time.sleep(0.2)
        self.handler()

    def readlines(self):
        return self.handler()

    def handler(self):
        if self.command == b'?\n': return self.help()
        elif self.command == b'raw\n': return self.raw()
        elif self.command == b'display\n': return self.display()
        elif self.command.startswith(b'sense'): return self.sense(self.command[5:].decode())
        elif self.command.startswith(b'hid'): return self.hid(self.command[4:-1].decode())
        elif self.command.startswith(b'aime'): return self.aime(self.command[4:-1].decode())
        else: return self.unknown()

    def help(self):
        response = ['\t<<Mai Pico Controller>>\r\n','https://...\r\n','\tSN: SimulatingDevice\r\n','Built: November 7, 2024\n','Available commands:...\r\n']
        return [i.encode() for i in response]

    def unknown(self):
        response = [b'Unknown command.\r\n'] + self.help()

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
                    '   Joy: on, NKRO: off\r\n' if self.hid_mode == "io4" else f'   Joy: off, NKRO: {self.hid_mode}\r\n',
                    '[AIME]\r\n',
                    f'  NFC Module: {self.aime_module}\r\n',
                    f'  Virtual AIC: {self.aime_virtual_aic.upper()}\r\n',
                    f'  Protocol Mode: {self.aime_protocol_mode}\r\n',
                    'mai_pico>']
        return [i.encode() for i in response]

    def sense(self, args):
        arg = args.split()
        if len(arg) == 1:
            if arg[0] == "0":   self.global_sense_adjusts = 0
            elif arg[0] == "+": self.global_sense_adjusts += 1
            elif arg[0] == "-": self.global_sense_adjusts -= 1
        elif len(arg) == 2:
            if arg[1] == "0":   self.sense_adjusts[SENSOR_INFO.index(arg[0])] = 0
            elif arg[1] == "+": self.sense_adjusts[SENSOR_INFO.index(arg[0])] += 1
            elif arg[1] == "-": self.sense_adjusts[SENSOR_INFO.index(arg[0])] -= 1
        print(f"[Cli device] Global {self.global_sense_adjusts:+}\n  {self.sense_adjusts}")
        return [b'Save requested.\r\n']

    def hid(self, arg):
        if arg in ("key1","key2","joy", "io4"): self.hid_mode = arg
        return [b'Save requested.\r\n']

    def aime(self, args):
        arg = args.split()
        if args == "": return [b'aime', b'Usage:...\r\n']
        if arg[0] == "virtual":
            self.aime_virtual_aic = arg[1]
        elif arg[0] == "mode":
            self.aime_protocol_mode = arg[1]
        return [b'Save requested.\r\n']

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

class Operating:
    def __init__(self, port, timeout=None):
        self.port = port

    def __enter__(self):
        return self.port

    def __exit__(self, exc_type, exc_val, exc_tb):
        return

    # def write(self, command):
        # self.port.write(command)

if __name__ == "__main__":
    cli = CliDevice()
    touch = TouchDevice()
    cli.write(b"hid key2\n")
    cli.write(b"display\n")
    print(cli.readlines())
