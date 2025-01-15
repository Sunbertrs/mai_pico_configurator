from PIL import Image, ImageDraw

from preset_var import canvas_size, CANVAS_FONT_SET, SENSOR_INFO, config_file, area_title_position, area_subtitl_position
from communication import get_sensor_raw_readings, get_sensor_sense_adjust, combine_raw_and_sense_adjust, get_sensor_touch

SHOW_SENSE_ADJUST = config_file["always_show_sense_adjust"]
INTERVAL_TIME = config_file["raw_readings_interval_time"]

AREA_ACT_CANVAS = []
rotate_angle = 0

for i, area in enumerate(SENSOR_INFO):
    exec(f'AREA_ACT_CANVAS.append(Image.open("images/canvas{area[0]}.png"))')
    AREA_ACT_CANVAS[-1] = AREA_ACT_CANVAS[-1].rotate(rotate_angle)
    if canvas_size == 1080:
        AREA_ACT_CANVAS[-1] = AREA_ACT_CANVAS[-1].resize((canvas_size,) * 2)
    else:
        AREA_ACT_CANVAS[-1] = AREA_ACT_CANVAS[-1].resize((canvas_size,) * 2)
    rotate_angle = rotate_angle - 45 if area[0] != "C" else rotate_angle - 180

def draw_text():
    sensor_name_stat = Image.new("RGBA", (1080, 1080))
    draw = ImageDraw.Draw(sensor_name_stat)
    raw_readings = combine_raw_and_sense_adjust(get_sensor_raw_readings(), get_sensor_sense_adjust()) if SHOW_SENSE_ADJUST else get_sensor_raw_readings()
    for title, pos in area_title_position.items():
        draw.text(pos, title, font=CANVAS_FONT_SET[0], fill="#000")
    for subtitl, pos in zip(raw_readings, area_subtitl_position.values()):
        draw.text(pos, subtitl, font=CANVAS_FONT_SET[1], fill="#000")
    return sensor_name_stat.resize((canvas_size,) * 2)

def draw_touch():
    touch_readings = get_sensor_touch()
    if not touch_readings:
        return 0
    touch_images_list = []
    for i, area in enumerate(touch_readings):
        if area == 1:
            touch_images_list.append(AREA_ACT_CANVAS[i])
    return touch_images_list