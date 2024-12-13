import sys
import threading
sys.path.insert(0, sys.path[0].replace("cmds",""))
from PIL import Image, ImageDraw

from preset_var import canvas_size, sensor_titles_fontset, sensor_info, cmds_sense_text
from communication import get_sensor_sense_adjust, adjust_sense_reset, adjust_sense

_inst = None

def main(instance):
    global _inst
    _inst = instance
    _inst.stop_draw_text = 1

    prompt_image = Image.new("RGBA", (1080,1080))
    draw = ImageDraw.Draw(prompt_image)
    draw.text((200,800), cmds_sense_text[0], font=sensor_titles_fontset[1])
    
    prompt_image = prompt_image.resize((canvas_size,)*2)
    _inst.canvas_handler.set_text(prompt_image)

    _inst.root.bind("<KeyPress-Escape>", lambda _: _inst.done_command("esc") )
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
    draw.text((520,520), pressed_key, font=sensor_titles_fontset[0])
    
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
        draw.text((510,520), selected_area, font=sensor_titles_fontset[0])
    else:
        draw.text((460,520), "Global", font=sensor_titles_fontset[0])
    
    draw.text((200,800), cmds_sense_text[1], font=sensor_titles_fontset[1])

    prompt_image_edited = prompt_image.copy()
    draw = ImageDraw.Draw(prompt_image_edited)
    
    adjusts_value:str = get_sensor_sense_adjust(index=sensor_info.index(selected_area)) if selected_area != "g" else get_sensor_sense_adjust(index=selected_area)

    if adjusts_value != "0":
        draw.text((520,600), adjusts_value, font=sensor_titles_fontset[0])
    else:
        draw.text((530,600), adjusts_value, font=sensor_titles_fontset[0])

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

    if value != 0:
        draw.text((520,600), f"{value:+}", font=sensor_titles_fontset[0])
    else:
        draw.text((530,600), "0", font=sensor_titles_fontset[0])

    prompt_image = prompt_image.resize((canvas_size,)*2)
    _inst.canvas_handler.set_text(prompt_image)
    
    _inst.root.bind("<KeyPress-Left>", lambda _: sensitivity_adjusting(image, area, "-", value))
    _inst.root.bind("<KeyPress-Right>", lambda _: sensitivity_adjusting(image, area, "+", value))
    _inst.root.bind("<KeyPress-Return>", lambda _: apply_sensitivity_settings(area, value))
    return

def apply_sensitivity_settings(area, value):
    _inst.root.unbind("<KeyPress-Escape>")
    _inst.root.unbind("<KeyPress-Left>")
    _inst.root.unbind("<KeyPress-Right>")
    _inst.root.unbind("<KeyPress-BackSpace>")
    _inst.root.unbind("<KeyPress-Return>")
    # _inst.stop_draw_touch = 1
    adjust_sense_reset(area)
    adjust_sense(area, value)
    threading.Thread(target=_inst.done_command, args=("sense",)).start()

if __name__ == "__main__":
    import tkinter as tk
    from PIL import ImageTk
    from communication import create_connection

    class Test:
        def __init__(self, root):
            self.root = root
            self.c = tk.Canvas(self.root, width=canvas_size, height=canvas_size, bg="black")
            self.c.pack()
            self.canvas_handler = EditSensorCanvas(self.c)
            main(self)
            root.mainloop()

    class EditSensorCanvas:
        def __init__(self, sensor_canvas):
            self.sensor_canvas = sensor_canvas

        def set_text(self, image):
            self.sensor_text_photoimage = ImageTk.PhotoImage(image)
            if self.sensor_canvas.find_withtag('text'):
                self.sensor_canvas.delete('text')
            self.sensor_canvas.create_image(canvas_size/2, canvas_size/2, image=self.sensor_text_photoimage, tag='text')

        def set_touch(self, imagelist):
            if len(imagelist) == 0:
                self.sensor_canvas.delete("touch")
                return
            try:
                if len(self.sensor_touch_prev) != 0 and self.sensor_touch_prev == imagelist:
                    return
            except AttributeError:
                pass
            self.sensor_canvas.delete("touch")
            sensor_touch_stat = Image.new('RGBA', (canvas_size,)*2)
            for i in imagelist:
                sensor_touch_stat.paste(i, (0,0), i)
            self.sensor_touch_photoimage = ImageTk.PhotoImage(sensor_touch_stat)
            self.sensor_canvas.create_image(canvas_size/2, canvas_size/2, image=self.sensor_touch_photoimage, tag="touch")
            self.sensor_canvas.tag_raise("text")

            self.sensor_touch_prev = imagelist

    # create_connection()
    a = Test(tk.Tk())