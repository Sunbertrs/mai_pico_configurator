import serial
import yaml
import re

from preset_var import sensor_area, no_device_debug

def check_connect():
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    if config['cli_port'] == config['touch_port'] == '':
        return ('Not_set',)
    if no_device_debug:
        print("No device debug mode is enabled.")
        return (1,)

    try:
        cli = serial.Serial(config['cli_port'])
        touch = serial.Serial(config['touch_port'])
    except serial.serialutil.SerialException as e:
        stat =  (0, e)
    else:
        cli.close()
        touch.close()
        stat = (1,)
    finally:
        return stat

def create_connection():
    global cli_port, touch_port, operating
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    if not no_device_debug:
        operating = serial.Serial
        cli_port = config['cli_port']
        touch_port = config['touch_port']
    else:
        import device_simulate
        operating = device_simulate.Operating
        cli_port = device_simulate.CliDevice()
        touch_port = device_simulate.TouchDevice()

def get_hardware_basic_info():
    with operating(cli_port, timeout=0.2) as port:
        port.write(b'?\n')
        response = [i.decode().strip() for i in port.readlines()[:8]]
        basic_info = [i for i in response if "SN" in i][0]
    try:
        basic_info = basic_info + "\n" + [i for i in response if "Built" in i][0]
    except IndexError:
        pass
    basic_info = basic_info + f"\nCli: {cli_port}; Touch: {touch_port}"
    basic_info = basic_info + f"\nBrightness level: " + get_brightness_level()
    basic_info = basic_info + f"\nGlobal sensitivity: " + get_sensor_sense_adjust(index='g')
    hid_stat = get_hid_mode()
    basic_info = basic_info + f"\nHID mode: " + ("!!! Button is stuck, force using io4 now !!!" if hid_stat[-1] == "!" else hid_stat)
    basic_info = basic_info + f"\nNFC module: " + get_aime_info()

    return basic_info

def get_sensor_raw_readings():
    with operating(cli_port, timeout=0.2) as port:
        port.write(b'raw\n')
        response = [i.decode().strip() for i in port.readlines()]
        raw_info = []

    for area in sensor_area:
        for readings in response:
            if area in readings: raw_info = raw_info + [i.strip() for i in readings.split("|")[1:-1]]

    return raw_info

def get_sensor_sense_adjust(index=None):
    with operating(cli_port, timeout=0.2) as port:
        port.write(b'display\n')
        response = [i.decode().strip() for i in port.readlines()]
        response = response[response.index("[Sense]")+1:response.index("[Sense]")+10]
        sense_adjust_info = []
    for line in response:
        if index == "g" and "global" in line:
            global_adjust = re.sub("[^\\+\\-0-9]", "", line)
            if global_adjust == "+0": global_adjust = "0"
            return global_adjust
        for area in sensor_area:
            if area in line:
                sense_adjust_info = sense_adjust_info + [i.strip() for i in line.split("|")[1:-1]]
    for i, adjust in enumerate(sense_adjust_info):
        if adjust != "0":
            sense_adjust_info[i] = f"+{sense_adjust_info[i]}" if len(sense_adjust_info[i]) == 1 else f"-{256-int(sense_adjust_info[i])}"
        else:
            sense_adjust_info[i] = "0"
    if index is None:
        return sense_adjust_info
    else:
        return sense_adjust_info[index]

def combine_raw_and_sense_adjust(raw, adjust):
    result = raw
    for i, adjust in enumerate(adjust):
        if adjust != "0": result[i] = f"{result[i]}({adjust})"

    return result

def adjust_sense_reset(area):
    with operating(cli_port, timeout=0.2) as port:
        if area == "g":
            port.write(b'sense 0\n')
        else:
            port.write(f'sense {area} 0\n'.encode())
        port.readlines()

def adjust_sense(area, value):
    stat = "+" if value > 0 else "-"
    for _ in range(abs(value)):
        if area == "g":
            with operating(cli_port, timeout=0.2) as port: port.write(f'sense {stat}\n'.encode())
        else:
            with operating(cli_port, timeout=0.2) as port: port.write(f'sense {area} {stat}\n'.encode())
    with operating(cli_port, timeout=0.2) as port: port.readlines()

def get_hid_off_mode_availability():
    with operating(cli_port, timeout=0.2) as port:
        port.write(b'hid\n')
        response = [i.decode().strip() for i in port.readlines()]
    if "off" in response[0]:
        return 1
    else:
        return 0

def get_hid_mode(ignore_stuck=None):
    with operating(cli_port, timeout=0.2) as port:
        port.write(b'display\n')
        response = [i.decode().strip() for i in port.readlines()]
        response = response[response.index("[HID]")+1:response.index("[HID]")+3]
    if "Joy: on" in response or "IO4: on" in response[0]:
        stat = "io4"
    else:
        stat = response[0][response[0].index("key"):response[0].index("key")+4]
    if not ignore_stuck and response[1].startswith("!!!"):
        stat += "!"
    return stat

def adjust_hid_mode(mode):
    with operating(cli_port, timeout=0.2) as port:
        port.write(f'hid {mode}\n'.encode())
        port.readlines()

def get_aime_info(more=None):
    with operating(cli_port, timeout=0.2) as port:
        port.write(b'aime\n')
        response = [i.decode().strip() for i in port.readlines()]
    if response[1] == "Unknown command.":
        return "Unsupported"
    with operating(cli_port, timeout=0.2) as port:
        port.write(b'display\n')
        response = [i.decode().strip() for i in port.readlines()]
        response = response[response.index("[AIME]")+1:response.index("[AIME]")+4]
    if not more:
        return response[0].replace('NFC Module: ','')
    else:
        return (
            response[1].replace('Virtual AIC: ',''),
            response[2].replace('Protocol Mode: ','')
        )

def adjust_aime_virtual_aic(value):
    with operating(cli_port, timeout=0.2) as port:
        port.write(f'aime virtual {value.lower()}\n'.encode())
        port.readlines()

def adjust_aime_protocol_mode(value):
    with operating(cli_port, timeout=0.2) as port:
        port.write(f'aime mode {value}\n'.encode())
        port.readlines()

def get_brightness_level():
    with operating(cli_port, timeout=0.2) as port:
        port.write(b'display\n')
        response = [i.decode().strip() for i in port.readlines()]
        response = response[response.index("[RGB]")+3].replace("Level: ", "")
        return response

def adjust_brightness_level(value):
    with operating(cli_port, timeout=0.2) as port:
        port.write(f'level {value}\n'.encode())
        port.readlines()

# Thanks to @CVSJason(Github) for the reference on touch port communication implementation
def init_sensor_touch():
    with operating(touch_port, timeout=0.2) as port:
        port.write(b'{RSET}')
        port.write(b'{HALT}')
        port.write(b'{LAr2}')
        for area in range(0x41+0x01, 0x62+0x01):
            port.write(b'{L' + bytes([area]) + b'r2}')
        for area in range(0x41, 0x62+0x01):
            port.write(b'{L' + bytes([area]) + b'k'+ bytes([0x28]) + b'}')
        port.write(b'{STAT}')

        response = []
        while len(response) < 9:
            response.append(port.read())
            if len(response) == 9 and response[0] != b'(' and response[-1] != b')':
                del response[0]
    return 1

def get_sensor_touch():
    with operating(touch_port, timeout=0.2) as port:
        response = port.read(9)
    if response == b'': return
    results = []
    for i in range(1, 9):
        results.append(1 if response[i] & 0b1 != 0 else 0)
        results.append(1 if response[i] & 0b10 != 0 else 0)
        results.append(1 if response[i] & 0b100 != 0 else 0)
        results.append(1 if response[i] & 0b1000 != 0 else 0)
        results.append(1 if response[i] & 0b10000 != 0 else 0)
    return results[0:34]

def stop_get_touch_info():
    with operating(touch_port, timeout=0.2) as port:
        port.write(b'{RSET}')
        port.write(b'{HALT}')
    return

def program_update():
    stop_get_touch_info()
    with operating(cli_port, timeout=0.2) as port:
        port.write(b'update\n')
        try:
            port.readlines()
        except Exception:
            pass
    return

if __name__ == "__main__":
    create_connection()
    print(get_brightness_level())