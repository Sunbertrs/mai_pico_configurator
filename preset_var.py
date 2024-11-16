from PIL import ImageFont
import screeninfo

no_device_debug = False

def get_canvas_size():
    mornitor_info = screeninfo.get_monitors()
    size = 500
    if len(mornitor_info) > 1:
        for mornitor in mornitor_info:
            if mornitor.width < mornitor.height: size = 1080
    else:
        if mornitor_info[0].width < mornitor_info[0].height: size = 1080
    return size

canvas_size = get_canvas_size()

sensor_area = tuple([i for i in "ABCDE"])

sensor_number = tuple([i+1 for i in range(8)])

connect_stat = {
    0: "Program is not connect to port. Click the connect button to start.",
    1: "Program is running normally.",
    2: "Program is executing ",
    3: "",
}

buttons = {
    "Sensitivity adjust": 'cmds.sense',
    "LED brightness": 'cmds.level',
    "Buttons adjust": 'cmds',
    "Aime": 'cmds.aime',
    "Test": 'cmds',
    "Input mode": 'cmds',
    "Update firmware": 'cmds.update',
}

sensor_info = (
    "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8",
    "B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8",
    "C1", "C2",
    "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8",
    "E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8"
)

nkro_key = ("wedcxzaq", "89632147")

message_box_prompts = {
    "Denied": ("Error", "Unable to connect to the port, please make sure it is not in use."),
    "Reconfig": ("COM port reconfigured", "We reconfigured The port settings now because the config didn't configure correctly.\nThe program will now exit to update the settings.\n\nIf the port is still incorrect, please manually correct it in config.yaml."),
    "Not_detected": ("Error", "Failed to connect to the port, please make sure it is connected."),
    "Unable_execute": ("Error", "Unable execute this without device connected."),
    "Manual_port_repeat": ("Repeated value", "Value can't be the same."),
    "Manual_port_empty": ("Empty value", "Value can't be empty."),
    "Manual_port_fail": ("Failed to connect", "Please check your connection, or specify the correct port."),
    "Restart_sense": ("Restart required", "You may need to restart this program to get sensor touch showing.")
}

sensor_titles_fontset = (ImageFont.truetype("C:/Windows/Fonts/Consola.ttf", 53), ImageFont.truetype("C:/Windows/Fonts/msgothic.ttc", 30))

area_title_position = {
    "A1": (670,90),
    "A2": (910,310),
    "A3": (900,650),
    "A4": (670,900),
    "A5": (340,900),
    "A6": (110,660),
    "A7": (110,320),
    "A8": (340,90),
    "B1": (600,290),
    "B2": (710,410),
    "B3": (710,570),
    "B4": (590,690),
    "B5": (420,690),
    "B6": (300,570),
    "B7": (310,410),
    "B8": (420,290),
    "C1": (560,490),
    "C2": (450,490),
    "D1": (510,30),
    "D2": (830,170),
    "D3": (960,490),
    "D4": (820,810),
    "D5": (510,950),
    "D6": (200,810),
    "D7": (50,490),
    "D8": (180,170),
    "E1": (510,180),
    "E2": (730,280),
    "E3": (820,490),
    "E4": (730,710),
    "E5": (510,800),
    "E6": (290,710),
    "E7": (200,490),
    "E8": (290,280)
}

area_subtitl_position = {
    "A1": (680,150),
    "A2": (920,370),
    "A3": (910,710),
    "A4": (680,960),
    "A5": (350,960),
    "A6": (120,720),
    "A7": (120,380),
    "A8": (350,150),
    "B1": (610,350),
    "B2": (720,470),
    "B3": (720,630),
    "B4": (600,750),
    "B5": (430,750),
    "B6": (310,630),
    "B7": (320,470),
    "B8": (430,350),
    "C1": (570,550),
    "C2": (460,550),
    "D1": (520,90),
    "D2": (840,230),
    "D3": (970,550),
    "D4": (830,870),
    "D5": (520,1010),
    "D6": (210,870),
    "D7": (60,550),
    "D8": (190,230),
    "E1": (520,240),
    "E2": (730,330),
    "E3": (830,550),
    "E4": (730,770),
    "E5": (520,860),
    "E6": (300,770),
    "E7": (210,550),
    "E8": (300,330)
}
