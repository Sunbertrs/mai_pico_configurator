"""
Everything here builds PIL images only. The result is handed to
the sensor view, which scales it to fit.
"""

from __future__ import annotations

import os

from PIL import Image, ImageDraw

from preset_var import (
    CANVAS_CENTER_POSITION,
    CANVAS_FONT_SET,
    CMD_TITLE_POSITION,
    IMAGES_DIR,
    KEY_PROMPTING_POSITION,
    SENSOR_INFO,
    SETTINGS_SPACING,
    area_subtitl_position,
    area_title_position,
)

CANVAS_SIZE = 1080

AREA_TOUCH_LAYER = []
_rotate_angle = 0
for _area in SENSOR_INFO:
    _layer = Image.open(os.path.join(IMAGES_DIR, f"hilight{_area[0]}.png")).rotate(_rotate_angle)
    AREA_TOUCH_LAYER.append(_layer)
    _rotate_angle = _rotate_angle - 45 if _area[0] != "C" else _rotate_angle - 180


def readings_image(readings: list[str], adjust: list[str] | None) -> Image.Image:
    """
    Draw the area labels and their raw readings.
    """
    image = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE))
    painter = ImageDraw.Draw(image)

    for title, position in area_title_position.items():
        painter.text(position, title, font=CANVAS_FONT_SET[0], fill="#000")

    subtitle_list = readings
    if adjust is not None:
        for index, value in enumerate(adjust):
            if index < len(readings) and value != "0":
                subtitle_list[index] = f"{subtitle_list[index]}({value})"

    for value, position in zip(subtitle_list, area_subtitl_position.values()):
        painter.text(position, value, font=CANVAS_FONT_SET[1], fill="#333")
    return image


def touch_image(bits) -> Image.Image | None:
    """
    Compose the highlight overlay for the pressed areas.
    """
    if not bits or not any(bits):
        return None
    layer = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE))
    for index, pressed in enumerate(bits):
        if pressed and index < len(AREA_TOUCH_LAYER):
            layer = Image.alpha_composite(layer, AREA_TOUCH_LAYER[index])
    return layer


def draw_title_and_prompting_keys(painter, title_text, prompt_text, center=None):
    position = CANVAS_CENTER_POSITION if center else CMD_TITLE_POSITION
    painter.text(position, title_text, font=CANVAS_FONT_SET[0], anchor="mm", fill="#000")
    painter.text(KEY_PROMPTING_POSITION, prompt_text, font=CANVAS_FONT_SET[1], fill="#000")


def draw_selecting_options(painter, option_index, option_name, is_current):
    painter.text(
        (CMD_TITLE_POSITION[0], CMD_TITLE_POSITION[1] + SETTINGS_SPACING * option_index + 50),
        option_name,
        font=CANVAS_FONT_SET[2],
        anchor="mm",
        fill="#E00" if is_current else "#000",
    )


def resize_and_display(instance, image):
    """
    Hand a freshly drawn page to the sensor view; it does the scaling.
    """
    instance.canvas_handler.set_text(image)
