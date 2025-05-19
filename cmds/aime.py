from PIL import Image, ImageDraw
from tkinter import messagebox

from draw import draw_title_and_prompting_keys, draw_selecting_options, resize_and_display
from preset_var import message_box_prompts, cmds_aime_text, CANVAS_FONT_SET
from communication import get_aime_info, adjust_aime_virtual_aic, adjust_aime_protocol_mode

def main(instance):
    global _inst
    _inst = instance

    status = get_aime_info()
    if status == "Unsupported":
        messagebox.showerror(*message_box_prompts["Aime_unsupported"])
        _inst.done_command("esc")
        return

    global prompt_image
    prompt_image = Image.new("RGBA", (1080,1080))
    draw = ImageDraw.Draw(prompt_image)
    draw_title_and_prompting_keys(draw, cmds_aime_text[0], cmds_aime_text[3])
    draw_selecting_options(draw, 4, f"NFC module - {status}", 0)
    select_option(list(get_aime_info(more=1)), 0)

def select_option(settings, current):
    global aime_settings, prompt_image
    aime_settings = settings
    image = prompt_image.copy()
    draw = ImageDraw.Draw(image)
    for i, j in enumerate(cmds_aime_text[1:3], start=1):
        draw_selecting_options(draw, i, f'{j:<17}{aime_settings[i-1]:>3}', (current == i - 1))
    resize_and_display(_inst, image)
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
    _inst.done_command("refresh")