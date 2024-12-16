from threading import Thread
from PIL import Image, ImageDraw

from preset_var import canvas_size, sensor_titles_fontset, sensor_info, cmds_hid_text, key_prompt_position
from communication import adjust_hid_mode, get_hid_mode

def main(instance):
    global _inst
    _inst = instance
    _inst.stop_draw_text = 1

    prompt_image = Image.new("RGBA", (1080,1080))
    draw = ImageDraw.Draw(prompt_image)

    draw.text((540,300), cmds_hid_text[0], font=sensor_titles_fontset[0], anchor="mm")
    draw.text(key_prompt_position, cmds_hid_text[4], font=sensor_titles_fontset[1])

    selection(prompt_image, get_hid_mode())

def selection(image, current):
    draw = ImageDraw.Draw(image)
    draw.text((540,450), cmds_hid_text[1], font=sensor_titles_fontset[2], anchor="mm", fill="orange" if current == "io4" else "white")
    draw.text((540,530), cmds_hid_text[2], font=sensor_titles_fontset[2], anchor="mm", fill="orange" if current == "key1" else "white")
    draw.text((540,610), cmds_hid_text[3], font=sensor_titles_fontset[2], anchor="mm", fill="orange" if current == "key2" else "white")
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
    Thread(target=_inst.done_command, args=("refresh",)).start()