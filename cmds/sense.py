import sys
sys.path.insert(0, sys.path[0].replace("cmds",""))
from PIL import Image, ImageDraw

from draw import draw_title_and_prompting_keys, resize_and_display
from preset_var import CANVAS_FONT_SET, SENSOR_INFO, cmds_sense_text
from communication import get_sensor_sense_adjust, adjust_sense_reset, adjust_sense

SENSE_ADJUST_POSITION = (540,620)

def main(instance):
    global _inst
    _inst = instance

    prompt_image = Image.new("RGBA", (1080,1080))
    draw = ImageDraw.Draw(prompt_image)
    draw_title_and_prompting_keys(draw, cmds_sense_text[0], cmds_sense_text[1])
    resize_and_display(_inst, prompt_image)

    for i in "ABCDEabcde":
        _inst.root.bind(f'<KeyPress-{i}>', select_number)
    _inst.root.bind(f'<KeyPress-G>', lambda e: sensitivity_adjust(e.keysym.lower()))
    _inst.root.bind(f'<KeyPress-g>', lambda e: sensitivity_adjust(e.keysym))

def select_number(event):
    pressed_key = event.keysym.upper()
    for i in "ABCDEabcde":
        _inst.root.unbind(f'<KeyPress-{i}>')
    
    prompt_image = Image.new("RGBA", (1080,1080))
    draw = ImageDraw.Draw(prompt_image)
    draw_title_and_prompting_keys(draw, cmds_sense_text[0], "")
    draw_title_and_prompting_keys(draw, pressed_key, "", center=1)
    
    resize_and_display(_inst, prompt_image)

    for i in "12345678":
        if pressed_key == "C" and i == "3": break
        _inst.root.bind(f'<KeyPress-{i}>', lambda e: sensitivity_adjust(f'{pressed_key}{e.keysym}'))
    _inst.root.bind("<KeyPress-BackSpace>", lambda _: main(_inst))

def sensitivity_adjust(selected_area):
    for i in "12345678":
        _inst.root.unbind(f'<KeyPress-{i}>')
    
    prompt_image = Image.new("RGBA", (1080,1080))
    draw = ImageDraw.Draw(prompt_image)

    if selected_area != "g":
        draw_title_and_prompting_keys(draw, selected_area, "", center=1)
    else:
        draw_title_and_prompting_keys(draw, cmds_sense_text[3], "", center=1)

    draw_title_and_prompting_keys(draw, cmds_sense_text[0], cmds_sense_text[2])

    prompt_image_edited = prompt_image.copy()
    draw = ImageDraw.Draw(prompt_image_edited)

    adjusts_value:str = get_sensor_sense_adjust(index=SENSOR_INFO.index(selected_area)) if selected_area != "g" else get_sensor_sense_adjust(index=selected_area)

    draw.text(SENSE_ADJUST_POSITION, adjusts_value, font=CANVAS_FONT_SET[2], anchor="mm", fill="#E00")

    resize_and_display(_inst, prompt_image_edited)
    
    _inst.root.bind("<KeyPress-BackSpace>", lambda _: main(_inst))
    _inst.root.bind("<KeyPress-Left>", lambda _: sensitivity_adjusting(prompt_image, selected_area, "-", int(adjusts_value)))
    _inst.root.bind("<KeyPress-Right>", lambda _: sensitivity_adjusting(prompt_image, selected_area, "+", int(adjusts_value)))
    _inst.root.bind("<KeyPress-Return>", lambda _: _inst.done_command("esc"))

def sensitivity_adjusting(image, area, stat, value:int):
    value = value + 1 if stat == "+" else value - 1
    if value > 9: value = 9
    elif value < -9: value = -9
    prompt_image = image.copy()
    draw = ImageDraw.Draw(prompt_image)

    draw.text(SENSE_ADJUST_POSITION, f"{value:+}" if value != 0 else "0", font=CANVAS_FONT_SET[2], anchor="mm", fill="#E00")

    resize_and_display(_inst, prompt_image)
    
    _inst.root.bind("<KeyPress-Left>", lambda _: sensitivity_adjusting(image, area, "-", value))
    _inst.root.bind("<KeyPress-Right>", lambda _: sensitivity_adjusting(image, area, "+", value))
    _inst.root.bind("<KeyPress-Return>", lambda _: apply_sensitivity_settings(area, value))
    return

def apply_sensitivity_settings(area, value):
    _inst.root.unbind("<KeyPress-Left>")
    _inst.root.unbind("<KeyPress-Right>")
    _inst.root.unbind("<KeyPress-BackSpace>")
    _inst.root.unbind("<KeyPress-Return>")
    adjust_sense_reset(area)
    adjust_sense(area, value)
    _inst.done_command("refresh")
