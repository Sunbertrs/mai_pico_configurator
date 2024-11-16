import time

from PIL import Image, ImageDraw
import yaml

import preset_var
from preset_var import canvas_size, sensor_titles_fontset, sensor_info
import communication
from communication import get_sensor_raw_readings, get_sensor_sense_adjust, combine_raw_and_sense_adjust, get_sensor_touch

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)
    SHOW_SENSE_ADJUST = config["always_show_sense_adjust"]
    INTERVAL_TIME = config["raw_readings_interval_time"]

already_get_adjusts = 0

def update_sense_adjusts():
    global already_get_adjusts, sense_adjusts
    sense_adjusts = get_sensor_sense_adjust()
    already_get_adjusts = 1

def draw_text():
    sensor_name_stat = Image.new("RGBA", (1080,1080))
    draw = ImageDraw.Draw(sensor_name_stat)
    if not already_get_adjusts: update_sense_adjusts()
    raw_readings = combine_raw_and_sense_adjust(get_sensor_raw_readings(), sense_adjusts) if SHOW_SENSE_ADJUST else sense_adjusts
    for title, pos in preset_var.area_title_position.items():
        draw.text(pos, title, font=sensor_titles_fontset[0])
    for subtitl, pos in zip(raw_readings, preset_var.area_subtitl_position.values()):
        draw.text(pos, subtitl, font=sensor_titles_fontset[1])

    time.sleep(INTERVAL_TIME)
    return sensor_name_stat.resize((canvas_size,)*2)

AREA_ACT_CANVAS = []
rotate_angle = 0
for i, area in enumerate(sensor_info):
    exec(f'AREA_ACT_CANVAS.append(Image.open("images/canvas{area[0]}.png"))')
    AREA_ACT_CANVAS[-1] = AREA_ACT_CANVAS[-1].rotate(rotate_angle)
    if canvas_size == 1080:
        AREA_ACT_CANVAS[-1] = AREA_ACT_CANVAS[-1].resize((canvas_size,)*2)
    else:
        AREA_ACT_CANVAS[-1] = AREA_ACT_CANVAS[-1].resize((canvas_size,)*2)
    rotate_angle = rotate_angle - 45 if area[0] != "C" else rotate_angle - 180

def draw_touch():
    touch_readings = get_sensor_touch()
    if not touch_readings:
        return 0
    touch_images = []
    for i, area in enumerate(touch_readings):
        if area == 1:
            touch_images.append(AREA_ACT_CANVAS[i])
    return touch_images