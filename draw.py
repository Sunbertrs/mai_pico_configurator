from PIL import Image, ImageDraw

from preset_var import canvas_size, CANVAS_FONT_SET, SENSOR_INFO, config_file, area_title_position, \
    area_subtitl_position, CMD_TITLE_POSITION, KEY_PROMPTING_POSITION, SETTINGS_SPACING, CANVAS_CENTER_POSITION
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
    try:
        info = (get_sensor_raw_readings(), get_sensor_sense_adjust())
    except Exception:
        return "Lost"
    raw_readings = combine_raw_and_sense_adjust(*info) if SHOW_SENSE_ADJUST else get_sensor_raw_readings()
    for title, pos in area_title_position.items():
        draw.text(pos, title, font=CANVAS_FONT_SET[0], fill="#000")
    for subtitl, pos in zip(raw_readings, area_subtitl_position.values()):
        draw.text(pos, subtitl, font=CANVAS_FONT_SET[1], fill="#000")
    return sensor_name_stat.resize((canvas_size,) * 2)

def draw_touch():
    try:
        touch_readings = get_sensor_touch()
    except Exception:
        return "Lost"
    if not touch_readings:
        return []

    touch_images_list = []
    for i, area in enumerate(touch_readings):
        if area == 1:
            touch_images_list.append(AREA_ACT_CANVAS[i])
    return touch_images_list

def draw_title_and_prompting_keys(draw, title_text, prompt_text, center=None):
    if not center:
        draw.text(CMD_TITLE_POSITION, title_text, font=CANVAS_FONT_SET[0], anchor="mm", fill="#000")
    else:
        draw.text(CANVAS_CENTER_POSITION, title_text, font=CANVAS_FONT_SET[0], anchor="mm", fill="#000")
    draw.text(KEY_PROMPTING_POSITION, prompt_text, font=CANVAS_FONT_SET[1], fill="#000")
    return

def draw_selecting_options(draw, option_index, option_name, is_current):
    draw.text((CMD_TITLE_POSITION[0], CMD_TITLE_POSITION[1] + SETTINGS_SPACING * option_index + 50),
              option_name,
              font=CANVAS_FONT_SET[2],
              anchor="mm",
              fill="#E00" if is_current else "#000"
    )
    return

def resize_and_display(_inst, image):
    if canvas_size != 1080:
        image = image.resize((500, 500))
    _inst.canvas_handler.set_text(image)