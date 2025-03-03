from PIL import Image, ImageDraw
from tkinter import messagebox

from communication import get_gpio_info, get_hid_mode, adjust_gpio_main_button, gpio_reset
from preset_var import CMD_TITLE_POSITION, cmds_gpio_text, CANVAS_FONT_SET, message_box_prompts, KEY_PROMPTING_POSITION, \
    area_title_position, SETTINGS_SPACING, canvas_size, area_subtitl_position, GPIO_DEFAULT_DEFINITION, NKRO_KEY, \
    CANVAS_CENTER_POSITION


def main(instance):
    global _inst
    _inst = instance

    status = get_gpio_info()
    if status == "Unsupported":
        messagebox.showerror(*message_box_prompts["Gpio_unsupported"])
        _inst.done_command("esc")
        return
    elif not get_hid_mode(ignore_stuck=1).startswith("key"):
        print(get_hid_mode())
        messagebox.showerror(*message_box_prompts["Gpio_not_nkro"])
        _inst.done_command("esc")
        return
    selecting(0)

def selecting(current):
    global prompt_image
    prompt_image = Image.new("RGBA", (1080, 1080))
    draw = ImageDraw.Draw(prompt_image)
    draw.text(CMD_TITLE_POSITION, cmds_gpio_text[0], font=CANVAS_FONT_SET[0], anchor="mm", fill="#000")
    draw.text(KEY_PROMPTING_POSITION, cmds_gpio_text[1], font=CANVAS_FONT_SET[1], fill="#000")
    for i, j in enumerate(cmds_gpio_text[2:5], start=1):
        draw.text((CMD_TITLE_POSITION[0],CMD_TITLE_POSITION[1]+SETTINGS_SPACING*i+50),
                  j,
                  font=CANVAS_FONT_SET[2],
                  anchor="mm",
                  fill="#E00" if current == i-1 else "#000"
        )
    image = prompt_image.resize((canvas_size,) * 2)
    _inst.canvas_handler.set_text(image)
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
    edit_main_button(None, 0, get_hid_mode(ignore_stuck=1)[-1])

def edit_main_button(detected_value, current, key_position):
    global gpio_definition
    if detected_value is not None:
        gpio_definition[current-1] = GPIO_DEFAULT_DEFINITION[NKRO_KEY[int(key_position)-1].index(detected_value)]
    image = prompt_image.copy()
    draw = ImageDraw.Draw(image)
    for i, j in zip(subtitl_display_position, enumerate(gpio_definition)):
        draw.text(i, j[1], font=CANVAS_FONT_SET[1], fill="#E00" if current == j[0] else "#000")
    for i in NKRO_KEY[int(key_position)-1]:
        _inst.root.bind(f'<KeyPress-{i}>', lambda a: edit_main_button(a.keysym, current+1, key_position))
    if current == 8:
        confirm_main_button(image, key_position)
    else:
        draw.text(KEY_PROMPTING_POSITION, cmds_gpio_text[5], fill="#000", font=CANVAS_FONT_SET[1])
    image = image.resize((canvas_size,) * 2)
    _inst.canvas_handler.set_text(image)

def confirm_main_button(image, key_position):
    for i in NKRO_KEY[int(key_position) - 1]:
        _inst.root.unbind(f'<KeyPress-{i}>')
    _inst.root.bind("<KeyPress-Return>", lambda _: apply_main_button())
    _inst.root.bind("<KeyPress-BackSpace>", lambda _:display_main_button())
    draw = ImageDraw.Draw(image)
    draw.text(CANVAS_CENTER_POSITION, cmds_gpio_text[6], fill="#000", font=CANVAS_FONT_SET[0], anchor="mm")
    draw.text(KEY_PROMPTING_POSITION, cmds_gpio_text[7], fill="#000", font=CANVAS_FONT_SET[1])

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
    draw.text(CANVAS_CENTER_POSITION, cmds_gpio_text[12], fill="#000", font=CANVAS_FONT_SET[0], anchor="mm")
    draw.text(KEY_PROMPTING_POSITION, cmds_gpio_text[7], fill="#000", font=CANVAS_FONT_SET[1])
    prompt_image = prompt_image.resize((canvas_size,)*2)
    _inst.canvas_handler.set_text(prompt_image)
    _inst.root.bind("<KeyPress-BackSpace>", lambda _: selecting(0))
    _inst.root.bind("<KeyPress-Return>", lambda _: reset_gpio())

def reset_gpio():
    gpio_reset()
    _inst.done_command("esc")