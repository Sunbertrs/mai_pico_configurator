from PIL import ImageFont
import screeninfo
import yaml
import subprocess

# no_device_debug = False

with open("config.yaml") as f:
    config_file = yaml.safe_load(f)

def get_canvas_size():
    monitor_info = screeninfo.get_monitors()
    size = 500
    if config_file["auto_large_ui"]:
        for monitor in monitor_info:
            if monitor.width < monitor.height: size = 1080
    return size

canvas_size = get_canvas_size()

def get_com_list():
    subprocess.run(['powershell', """
        $number = (Get-WMIObject Win32_PnPEntity | Where-Object {$_.name -match "com\\d"}).Name
        try{
            $name = (Get-WMIObject Win32_PnPEntity | Where-Object {$_.name -match "com\\d"}).GetDeviceProperties("DEVPKEY_Device_BusReportedDeviceDesc").deviceProperties.Data
        }catch{
            exit
        }
        $i=0
        foreach($num in $number){
            $num = $num -replace "[^com\\d\\d]", ""
            if($exist -eq 1){
                break
            }else{
                [PSCustomObject]@{ Number = $num; Name = $name[$i] } | Export-Csv -NoTypeInformation -Path ./com_list.csv -Append
                $exist=1
            }
            $i++
            $exist=0
        }
    """])

sensor_area = tuple([i for i in "ABCDE"])

SENSOR_INFO = (
    "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8",
    "B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8",
    "C1", "C2",
    "D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8",
    "E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8"
)

NKRO_KEY = ("wedcxzaq", "89632147")

GPIO_DEFAULT_DEFINITION = ("GP1", "GP0", "GP4", "GP5", "GP8", "GP9", "GP3", "GP2")

connect_stat = {
    0: "Click the connect button to start.",
    1: "Program is running normally.",
    2: "Program is executing ",
    3: "",
}

buttons = {
    "Sensitivity": 'cmds.sense',
    "LED brightness": 'cmds.level',
    "Aime": 'cmds.aime',
    "GPIO definition": 'cmds.gpio',
    "HID mode": 'cmds.hid',
    "Update firmware": 'cmds.update',
    "Factory reset": 'cmds.factory',
}

message_box_prompts = {
    "Denied": ("Error", "Unable to connect to the port, make sure it is not in use."),
    "Reconfig": ("COM port reconfigured", "Port settings have reconfigured, please click the connect button again to try.\nIf the port is still incorrect, please manually correct it in config.yaml."),
    "Not_detected": ("Error", "Failed to connect to the port, make sure it is connected, and Powershell is not disabled."),
    "Disconnected": ("Error", "Connection lost, please try again."),
    "Manual_port_repeat": ("Repeated value", "The value can't be the same."),
    "Manual_port_empty": ("Empty value", "The value can't be empty."),
    "Manual_port_illegal": ("Illegal value", "The value is illegal."),
    "Manual_port_fail": ("Failed to connect", "Please check your connection, or specify the correct port."),
    "Update_firmware": ("Exiting", "The program will now exit.\nPut your firmware file into the disk that appeared."),
    "Aime_unsupported": ("Failed to configure Aime", "The firmware you are using now does not support Aime.\nPlease upgrade to a newer version."),
    "Gpio_unsupported": ("Failed to configure GPIO", "The firmware you are using now does not support GPIO.\nPlease upgrade to a newer version."),
    "Gpio_not_nkro": ("Error", "Unavailable to configure GPIO definition in io4 mode."),
    "Factory_warning": ("Warning", "Are you sure to reset?All your settings will lost!\n(Including sensitivity, button reassignment, etc.)"),
    "Factory_done": ("Notice", "The settings have reset to default now.")
}

CANVAS_FONT_SET = (
    ImageFont.truetype("fonts/NotoSans.ttf", 53),
    ImageFont.truetype("fonts/NotoSans.ttf", 30),
    ImageFont.truetype("fonts/NotoSans.ttf", 41)
)

CMD_TITLE_POSITION = (540,300)

SETTINGS_SPACING = 85

KEY_PROMPTING_POSITION = (130,780)

CANVAS_CENTER_POSITION = (540,540)

area_title_position = {
    "A1": (670,90),
    "A2": (910,310),
    "A3": (900,650),
    "A4": (670,900),
    "A5": (340,900),
    "A6": (110,650),
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
    "E2": (730,270),
    "E3": (820,490),
    "E4": (730,710),
    "E5": (510,800),
    "E6": (290,710),
    "E7": (200,490),
    "E8": (290,270)
}

area_subtitl_position = {
    "A1": (680,150),
    "A2": (920,370),
    "A3": (910,720),
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

cmds_sense_text = (
    "Sensitivity configuration",
	"Type the area using your keyboard.\n\nPress 'g' for global sensitivity.",
	"Adjusting: Arrow <Left> or <Right>\n\nBack: <Backspace>\n\nApply: <Enter>",
    "Global"
)

cmds_hid_text = (
	"HID mode configuration",
    "Joy mode (io4)",
    "Default keyboard 1P",
    "Default keyboard 2P",
    "Off",
	"Switch option: Arrow <Up> or <Down>\n\nApply: <Enter>",
)

cmds_aime_text = (
	"Aime configuration",
    "Virtual AIC",
    "Protocol mode",
	"Switch option: Arrow <Up> or <Down>\n\nAdjust: Arrow <Left> or <Right>\n\nApply: <Enter>",
)

cmds_gpio_text = (
    "GPIO configuration",
    "Switch option: Arrow <Up> or <Down>\n\nApply: <Enter>",
    "Main buttons",
    "Aux buttons",
    "Reset all",
    #---
    "Press the button in the correct sequence now.\n\nBack: <Backspace>",
    "Apply?",
    "Yes: <Enter>\n\nNo: <Backspace>",
    #---
    "Test",
    "Service",
    "Square navigator",
    "Coin",
    #---
    "Are you sure to reset GPIO setting?",
)