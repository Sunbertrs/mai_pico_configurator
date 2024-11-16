import serial
import time
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
    global CLI_PORT, TOUCH_PORT
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    if not no_device_debug:
        CLI_PORT = serial.Serial(config['cli_port'], timeout=0.5)
        TOUCH_PORT = serial.Serial(config['touch_port'], timeout=0.15)
    else:
        import device_simulate
        CLI_PORT = device_simulate.CliDevice()
        TOUCH_PORT = device_simulate.TouchDevice()

def get_hardware_basic_info():
    with CLI_PORT as port:
        port.write(b'?\n')
        response = [i.decode().strip() for i in port.readlines()]
        basic_info = [i for i in response if "SN" in i ][0]

    try:
        basic_info = basic_info + "\n" + [i for i in response if "Built" in i][0]
    except IndexError:
        pass

    return basic_info

def get_sensor_raw_readings():
    with CLI_PORT as port:
        port.write(b'raw\n')
        response = [i.decode().strip() for i in port.readlines()]
        raw_info = []

    for area in sensor_area:
        for readings in response:
            if area in readings: raw_info = raw_info + [i.strip() for i in readings.split("|")[1:-1]]

    return raw_info

def get_sensor_sense_adjust(index=None):
    with CLI_PORT as port:
        port.write(b'display\n')
        response = [i.decode().strip() for i in port.readlines()[6:14]] # the grabbed [6:14] may not work in the latest firmware
        sense_adjust_info = []

    for line in response:
        if index == "g" and "global" in line:
            global_adjust = re.sub("[^\\+\\-0-9]", "", line)
            if global_adjust == "+0": global_adjust = "0"
            break
        for area in sensor_area:
            if area in line: sense_adjust_info = sense_adjust_info + [i.strip() for i in line.split("|")[1:-1]]

    for i, adjust in enumerate(sense_adjust_info):
        if adjust != "0":
            sense_adjust_info[i] = f"+{sense_adjust_info[i]}" if len(sense_adjust_info[i]) == 1 else f"-{256-int(sense_adjust_info[i])}"
        else:
            sense_adjust_info[i] = "0"

    if index is None:
        return sense_adjust_info
    elif index == "g":
        return global_adjust
    else:
        return sense_adjust_info[index]

def combine_raw_and_sense_adjust(raw, adjust):
    result = raw
    for i, adjust in enumerate(adjust):
        if adjust != "0": result[i] = f"{result[i]}({adjust})"

    return result

# Thanks to @CVSJason(Github) for the reference on touch port communication implementation
def init_sensor_touch():
    with TOUCH_PORT as port:
        port.write(b'{RSET}')
        port.write(b'{HALT}')
        port.write(b'{LAr2}')
        # while touch.read(6) != b'(LAr2)':
        #     time.sleep(0.5)
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
    with TOUCH_PORT as port:
        response = port.read(9)
    if response == b'': return
    # if not response.startswith(b'('): response = b'(' + touch.read(8) # The response will get offset if process get lag
    results = []
    for i in range(1, 9):
        results.append(1 if response[i] & 0b1 != 0 else 0)
        results.append(1 if response[i] & 0b10 != 0 else 0)
        results.append(1 if response[i] & 0b100 != 0 else 0)
        results.append(1 if response[i] & 0b1000 != 0 else 0)
        results.append(1 if response[i] & 0b10000 != 0 else 0)
    return results[0:34]

def stop_get_touch_info():
    with TOUCH_PORT as port:
        port.write(b'{HALT}')
    return

def stop_get_sensor_info():
    # touch.write(b'{HALT}')
    # touch.close()
    # cli.close()
    # return
    pass

def program_update():
    with TOUCH_PORT as port:
        port.write(b'{HALT}')
    with CLI_PORT as port:
        port.write(b'update\n')
    time.sleep(0.01)
    return

def adjust_sense_reset(area):
    with CLI_PORT as port:
        if area == "g":
            port.write(b'sense 0\n')
        else:
            port.write(f'sense {area} 0\n'.encode())
    time.sleep(0.01)

def adjust_sense(area, value):
    stat = "+" if value > 0 else "-"
    if area == "g":
        for _ in range(abs(value)):
            with CLI_PORT as port: port.write(f'sense {stat}\n'.encode())
            time.sleep(0.1)
    else:
        for _ in range(abs(value)):
            with CLI_PORT as port: port.write(f'sense {area} {stat}\n'.encode())
            time.sleep(0.1)

if __name__ == "__main__":
    create_connection()
    init_sensor_touch()