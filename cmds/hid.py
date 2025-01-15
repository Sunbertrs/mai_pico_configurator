from PIL import Image, ImageDraw

from preset_var import canvas_size, CANVAS_FONT_SET, cmds_hid_text, KEY_PROMPTING_POSITION, CMD_TITLE_POSITION, SETTINGS_SPACING
from communication import adjust_hid_mode, get_hid_mode

def main(instance):
    global _inst
    _inst = instance

    prompt_image = Image.new("RGBA", (1080,1080))
    draw = ImageDraw.Draw(prompt_image)

    draw.text(CMD_TITLE_POSITION, cmds_hid_text[0], font=CANVAS_FONT_SET[0], anchor="mm", fill="#000")
    draw.text(KEY_PROMPTING_POSITION, cmds_hid_text[4], font=CANVAS_FONT_SET[1], fill="#000")

    selection(prompt_image, get_hid_mode(ignore_stuck=1))

def selection(image, current):
    draw = ImageDraw.Draw(image)
    for i, j in enumerate(("io4", "key1", "key2"), start=1):
        draw.text((CMD_TITLE_POSITION[0],CMD_TITLE_POSITION[1]+SETTINGS_SPACING*i+50),
                  cmds_hid_text[i],
                  font=CANVAS_FONT_SET[2],
                  anchor="mm",
                  fill="#E00" if current == j else "#000")
    prompt_image = image.resize((canvas_size,) * 2)
    _inst.canvas_handler.set_text(prompt_image)

    if current == "io4":
        _inst.root.bind("<KeyPress-Down>", lambda _: selection(image, "key1"))
    elif current == "key1":
        _inst.root.bind("<KeyPress-Up>", lambda _: selection(image, "io4"))
        _inst.root.bind("<KeyPress-Down>", lambda _: selection(image, "key2"))
    elif current == "key2":
        _inst.root.bind("<KeyPress-Up>", lambda _: selection(image, "key1"))
    _inst.root.bind("<KeyPress-Return>", lambda _: apply_hid(current))

def apply_hid(current):
    _inst.root.unbind("<KeyPress-Up>")
    _inst.root.unbind("<KeyPress-Down>")
    _inst.root.unbind("<KeyPress-Return>")
    if current != get_hid_mode():
        adjust_hid_mode(current)
    _inst.done_command("refresh")