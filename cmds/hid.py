from PIL import Image, ImageDraw

from preset_var import canvas_size, CANVAS_FONT_SET, cmds_hid_text, KEY_PROMPTING_POSITION, CMD_TITLE_POSITION, SETTINGS_SPACING
from communication import adjust_hid_mode, get_hid_mode, get_hid_off_mode_availability

hid_off_mode = get_hid_off_mode_availability()

def main(instance):
    global _inst
    _inst = instance

    global prompt_image
    prompt_image = Image.new("RGBA", (1080,1080))
    draw = ImageDraw.Draw(prompt_image)

    draw.text(CMD_TITLE_POSITION, cmds_hid_text[0], font=CANVAS_FONT_SET[0], anchor="mm", fill="#000")
    draw.text(KEY_PROMPTING_POSITION, cmds_hid_text[5], font=CANVAS_FONT_SET[1], fill="#000")

    selection(get_hid_mode(ignore_stuck=1))

def selection(current):
    global prompt_image
    draw = ImageDraw.Draw(prompt_image)
    option = ("io4", "key1", "key2") + (("off",) if hid_off_mode else ())
    for i, j in enumerate(option, start=1):
        draw.text((CMD_TITLE_POSITION[0],CMD_TITLE_POSITION[1]+SETTINGS_SPACING*i+50),
                  cmds_hid_text[i],
                  font=CANVAS_FONT_SET[2],
                  anchor="mm",
                  fill="#E00" if current == j else "#000"
        )
    image = prompt_image.resize((canvas_size,) * 2)
    _inst.canvas_handler.set_text(image)

    if current == "io4":
        _inst.root.bind("<KeyPress-Down>", lambda _: selection("key1"))
    elif current == "key1":
        _inst.root.bind("<KeyPress-Up>", lambda _: selection("io4"))
        _inst.root.bind("<KeyPress-Down>", lambda _: selection("key2"))
    elif current == "key2":
        _inst.root.bind("<KeyPress-Up>", lambda _: selection("key1"))
        if len(option) == 4: _inst.root.bind("<KeyPress-Down>", lambda _: selection("off"))
    elif current == "off":
        _inst.root.bind("<KeyPress-Up>", lambda _: selection("key1"))
    _inst.root.bind("<KeyPress-Return>", lambda _: apply_hid(current))

def apply_hid(current):
    _inst.root.unbind("<KeyPress-Up>")
    _inst.root.unbind("<KeyPress-Down>")
    _inst.root.unbind("<KeyPress-Return>")
    if current != get_hid_mode():
        adjust_hid_mode(current)
    _inst.done_command("refresh")