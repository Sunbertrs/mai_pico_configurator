from PIL import Image, ImageDraw
from tkinter import messagebox

from communication import get_gpio_info, get_hid_mode, adjust_gpio_main_button, gpio_reset
from draw import draw_title_and_prompting_keys, draw_selecting_options, resize_and_display
from preset_var import cmds_gpio_text, CANVAS_FONT_SET, message_box_prompts, area_title_position, area_subtitl_position, GPIO_DEFAULT_DEFINITION, NKRO_KEY

def main(instance):
    global _inst
    _inst = instance

    status = get_gpio_info()
    if status == "Unsupported":
        messagebox.showerror(*message_box_prompts["Gpio_unsupported"])
        _inst.done_command("esc")
        return
    elif not get_hid_mode(ignore_stuck=1).startswith("key"):
        messagebox.showerror(*message_box_prompts["Gpio_not_nkro"])
        _inst.done_command("esc")
        return
    selecting(0)

def selecting(current):
    global prompt_image
    prompt_image = Image.new("RGBA", (1080, 1080))
    draw = ImageDraw.Draw(prompt_image)
    draw_title_and_prompting_keys(draw, cmds_gpio_text[0], cmds_gpio_text[1])
    for i, j in enumerate(cmds_gpio_text[2:5], start=1):
        draw_selecting_options(draw, i, j, (current==i-1))
    resize_and_display(_inst, prompt_image)
    if current == 0:
        _inst.root.bind("<KeyPress-Down>", lambda _: selecting(1))
    elif current == 1:
        _inst.root.bind("<KeyPress-Up>", lambda _: selecting(0))
        _inst.root.bind("<KeyPress-Down>", lambda _: selecting(2))
    elif current == 2:
        _inst.root.bind("<KeyPress-Up>", lambda _: selecting(1))
    _inst.root.bind("<KeyPress-Return>", lambda _: function_index(current))

def function_index(index):
    global gpio_definition
    if index == 0:
        gpio_definition = get_gpio_info()
        display_main_button()
    elif index == 1:
        gpio_definition = get_gpio_info(aux=1)
        edit_aux_button()
    else:
        confirm_reset_gpio()

def display_main_button():
    global prompt_image
    _inst.root.unbind("<KeyPress-Down>")
    prompt_image = Image.new("RGBA", (1080,1080))
    draw = ImageDraw.Draw(prompt_image)
    title_display_position = [i[1] for i in area_title_position.items() if i[0].startswith("A")]
    global subtitl_display_position
    subtitl_display_position = [i[1] for i in area_subtitl_position.items() if i[0].startswith("A")]
    for i, j in enumerate(title_display_position, start=1):
        draw.text(j, str(i), font=CANVAS_FONT_SET[0], fill="#000")
    _inst.root.bind("<KeyPress-BackSpace>", lambda _:selecting(0))
    edit_main_button("", 0, get_hid_mode(ignore_stuck=1)[-1])

def edit_main_button(detected_value, current, key_position):
    global gpio_definition
    if not detected_value.startswith("Insert"):
        if detected_value == "Reset":
            current = current - 1
        else:
            gpio_definition[current-1] = GPIO_DEFAULT_DEFINITION[NKRO_KEY[int(key_position)-1].index(detected_value)]
    else:
        gpio_definition[current-1] = detected_value.replace("Insert", "")
    image = prompt_image.copy()
    draw = ImageDraw.Draw(image)

    if detected_value.startswith("Insert") and len(detected_value) < 10: current = current - 1
    for i, j in zip(subtitl_display_position, enumerate(gpio_definition)):
        draw.text(i, j[1], font=CANVAS_FONT_SET[1], fill="#E00" if current == j[0] else "#000")
    if detected_value.startswith("Insert") and len(detected_value) < 10: current = current + 1

    for i in NKRO_KEY[int(key_position)-1]:
        _inst.root.bind(f'<KeyPress-{i}>', lambda a: edit_main_button(a.keysym, current+1, key_position))
    _inst.root.bind('<KeyPress-Insert>', lambda a: edit_main_button("InsertGP", current+1, key_position))

    if detected_value.startswith("Insert"):
        _inst.root.unbind('<KeyPress-Insert>')
        for i in NKRO_KEY[int(key_position)-1]:
            _inst.root.unbind(f'<KeyPress-{i}>')
        if len(detected_value) < 10:
            for i in range(10):
                _inst.root.bind(f'<KeyPress-{i}>', lambda a: edit_main_button(detected_value + a.keysym, current, key_position))
        elif len(detected_value) == 10 and int(detected_value[-2:]) <= 28 and gpio_definition[current] != gpio_definition[current-1]:
            for i in range(10):
                _inst.root.unbind(f'<KeyPress-{i}>')
            edit_main_button("Reset", current+1, key_position)
        elif len(detected_value) >= 10 and int(detected_value[-2:]) > 28:
            edit_main_button("InsertGP", current, key_position)

    if current == 8:
        confirm_main_button(image, key_position)
    else:
        draw_title_and_prompting_keys(draw, "", cmds_gpio_text[5])
    resize_and_display(_inst, image)

def confirm_main_button(image, key_position):
    for i in NKRO_KEY[int(key_position) - 1]:
        _inst.root.unbind(f'<KeyPress-{i}>')
    _inst.root.bind("<KeyPress-Return>", lambda _: apply_main_button())
    _inst.root.bind("<KeyPress-BackSpace>", lambda _:display_main_button())
    draw = ImageDraw.Draw(image)
    draw_title_and_prompting_keys(draw, cmds_gpio_text[6], cmds_gpio_text[7], center=1)

def apply_main_button():
    if gpio_definition != get_gpio_info():
        definition = " ".join(gpio_definition)
        definition = definition.replace("GP", "")
        adjust_gpio_main_button(definition)
    _inst.done_command("esc")

def edit_aux_button():
    pass

def confirm_reset_gpio():
    prompt_image = Image.new("RGBA", (1080, 1080))
    draw = ImageDraw.Draw(prompt_image)
    draw_title_and_prompting_keys(draw, cmds_gpio_text[12], cmds_gpio_text[7], center=1)
    resize_and_display(_inst, prompt_image)
    _inst.root.bind("<KeyPress-BackSpace>", lambda _: selecting(0))
    _inst.root.bind("<KeyPress-Return>", lambda _: reset_gpio())

def reset_gpio():
    gpio_reset()
    _inst.done_command("esc")