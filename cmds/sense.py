import sys
import threading
sys.path.insert(0, sys.path[0].replace("cmds",""))
from PIL import Image, ImageDraw

from preset_var import canvas_size, sensor_titles_fontset, sensor_info, cmds_sense_text, key_prompt_position, canvas_center_position
from communication import get_sensor_sense_adjust, adjust_sense_reset, adjust_sense

SENSE_ADJUST_POSITION = (540,620)

def main(instance):
    global _inst
    _inst = instance
    _inst.stop_draw_text = 1

    prompt_image = Image.new("RGBA", (1080,1080))
    draw = ImageDraw.Draw(prompt_image)
    draw.text(key_prompt_position, cmds_sense_text[0], font=sensor_titles_fontset[1])
    
    prompt_image = prompt_image.resize((canvas_size,)*2)
    _inst.canvas_handler.set_text(prompt_image)

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
    draw.text(canvas_center_position, pressed_key, font=sensor_titles_fontset[0], anchor="mm")
    
    prompt_image = prompt_image.resize((canvas_size,)*2)
    _inst.canvas_handler.set_text(prompt_image)

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
        draw.text(canvas_center_position, selected_area, font=sensor_titles_fontset[0], anchor="mm")
    else:
        draw.text(canvas_center_position, "Global", font=sensor_titles_fontset[0], anchor="mm")
    
    draw.text(key_prompt_position, cmds_sense_text[1], font=sensor_titles_fontset[1])

    prompt_image_edited = prompt_image.copy()
    draw = ImageDraw.Draw(prompt_image_edited)
    
    adjusts_value:str = get_sensor_sense_adjust(index=sensor_info.index(selected_area)) if selected_area != "g" else get_sensor_sense_adjust(index=selected_area)

    draw.text(SENSE_ADJUST_POSITION, adjusts_value, font=sensor_titles_fontset[2], anchor="mm")

    prompt_image_edited = prompt_image_edited.resize((canvas_size,)*2)
    _inst.canvas_handler.set_text(prompt_image_edited)
    
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

    draw.text(SENSE_ADJUST_POSITION, f"{value:+}" if value != 0 else "0", font=sensor_titles_fontset[2], anchor="mm")

    prompt_image = prompt_image.resize((canvas_size,)*2)
    _inst.canvas_handler.set_text(prompt_image)
    
    _inst.root.bind("<KeyPress-Left>", lambda _: sensitivity_adjusting(image, area, "-", value))
    _inst.root.bind("<KeyPress-Right>", lambda _: sensitivity_adjusting(image, area, "+", value))
    _inst.root.bind("<KeyPress-Return>", lambda _: apply_sensitivity_settings(area, value))
    return

def apply_sensitivity_settings(area, value):
    _inst.root.unbind("<KeyPress-Left>")
    _inst.root.unbind("<KeyPress-Right>")
    _inst.root.unbind("<KeyPress-BackSpace>")
    _inst.root.unbind("<KeyPress-Return>")
    # _inst.stop_draw_touch = 1
    adjust_sense_reset(area)
    adjust_sense(area, value)
    threading.Thread(target=_inst.done_command, args=("sense",)).start()
