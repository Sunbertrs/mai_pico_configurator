from threading import Thread
from PIL import Image, ImageDraw
from tkinter import messagebox

from preset_var import message_box_prompts, cmds_aime_text, sensor_titles_fontset, key_prompt_position, canvas_size
from communication import get_aime_info, adjust_aime_virtual_aic, adjust_aime_protocol_mode

def main(instance):
    global _inst
    _inst = instance
    _inst.stop_draw_text = 1

    status = get_aime_info()
    if status == "Unsupported":
        messagebox.showerror(*message_box_prompts["Aime_unsupported"])
        _inst.done_command("esc")
        return

    global prompt_image
    prompt_image = Image.new("RGBA", (1080,1080))
    draw = ImageDraw.Draw(prompt_image)

    draw.text((540,300), cmds_aime_text[0], font=sensor_titles_fontset[0], anchor="mm")
    draw.text(key_prompt_position, cmds_aime_text[3], font=sensor_titles_fontset[1])
    draw.text((540,640), f"NFC module - {status}", font=sensor_titles_fontset[2], anchor="mm")
    select_option(list(get_aime_info(more=1)), 0)

def select_option(settings, current):
    global aime_settings, prompt_image
    aime_settings = settings
    image = prompt_image.copy()
    draw = ImageDraw.Draw(image)
    draw.text((540,450), f"{cmds_aime_text[1]}{' '*8 if aime_settings[0] == 'OFF' else ' '*9}{aime_settings[0]}", font=sensor_titles_fontset[2], anchor="mm", fill="orange" if current == 0 else "white")
    draw.text((540,530), f"{cmds_aime_text[2]}{' '*5}{aime_settings[1]}", font=sensor_titles_fontset[2], anchor="mm", fill="orange" if current == 1 else "white")
    image = image.resize((canvas_size,)*2)
    _inst.canvas_handler.set_text(image)
    if current == 0:
        _inst.root.bind("<KeyPress-Down>", lambda _: select_option(aime_settings, 1))
    else:
        _inst.root.bind("<KeyPress-Up>", lambda _: select_option(aime_settings, 0))
    _inst.root.bind("<KeyPress-Left>", lambda _: adjust_option(current, aime_settings[current]))
    _inst.root.bind("<KeyPress-Right>", lambda _: adjust_option(current, aime_settings[current]))
    _inst.root.bind("<KeyPress-Return>", lambda _: apply_settings(aime_settings))

def adjust_option(current, setting):
    global aime_settings
    if current == 0:
        aime_settings[current] = "ON" if setting == "OFF" else "OFF"
    elif current == 1:
        aime_settings[current] = "1" if setting == "0" else "0"
    select_option(aime_settings, current)

def apply_settings(settings):
    original = get_aime_info(more=1)
    if tuple(settings) == original:
        _inst.done_command("esc")
        return
    if settings[0] != original[0]:
        adjust_aime_virtual_aic(settings[0])
    if settings[1] != original[1]:
        adjust_aime_protocol_mode(settings[1])
    Thread(target=_inst.done_command, args=("refresh",)).start()