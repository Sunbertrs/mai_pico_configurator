import sys
sys.path.insert(0, sys.path[0].replace("cmds",""))
from PIL import Image, ImageDraw
import threading

import preset_var
from preset_var import canvas_size, sensor_titles_fontset, sensor_area, sensor_number, sensor_info, area_title_position, area_subtitl_position, connect_stat
from communication import get_sensor_sense_adjust, adjust_sense_reset, adjust_sense

main_instance = None

def main(instance):
    global main_instance
    main_instance = instance
    instance.stop_draw_text.set()

    prompt_image = Image.new("RGBA", (1080,1080))
    draw = ImageDraw.Draw(prompt_image)
    draw.text((250,520), "Press the corresponding number to select.", font=sensor_titles_fontset[1])

    area_prompt_position = list(area_title_position.values())[0:6]
    select_prompt_position = list(area_subtitl_position.values())[0:6]

    for pos, area in zip(area_prompt_position, sensor_area+("Global",)):
        draw.text(pos, area, font=sensor_titles_fontset[0])
    for pos, num in zip(select_prompt_position, sensor_number[0:6]):
        draw.text(pos, f"Press {num}", font=sensor_titles_fontset[1])

    prompt_image = prompt_image.resize((canvas_size,)*2)
    instance.edit_canvas.set_sensor_text(prompt_image)

    instance.root.bind("<KeyPress-F2>", lambda a: instance.reset_thread_draw_text() )
    for i in sensor_number[0:5]:
        exec(f"instance.root.bind('<KeyPress-{i}>', lambda a: select_number(main_instance, {i}))")
    instance.root.bind('<KeyPress-6>', lambda a: sensitivity_adjust(main_instance, "g"))
    return

def select_number(instance, pressed_key):
    for i in sensor_number[0:6]:
        instance.root.unbind(f'<KeyPress-{i}>')

    prompt_image = Image.new("RGBA", (1080,1080))
    draw = ImageDraw.Draw(prompt_image)
    draw.text((520,520), sensor_area[pressed_key-1], font=sensor_titles_fontset[0])

    area_prompt_position = list(area_title_position.values())[0:8]
    select_prompt_position = list(area_subtitl_position.values())[0:8]

    for pos, num in zip(area_prompt_position, sensor_number):
        if pressed_key != 3:
            draw.text(pos, str(num), font=sensor_titles_fontset[0])
        else:
            if num == 3: break
            draw.text(pos, str(num), font=sensor_titles_fontset[0])

    prompt_image = prompt_image.resize((canvas_size,)*2)
    instance.edit_canvas.set_sensor_text(prompt_image)

    if pressed_key != 3:
        for i in sensor_number:
            exec(f"instance.root.bind('<KeyPress-{i}>', lambda a: sensitivity_adjust_thread(sensor_area[{pressed_key}-1]+str({i})) )")
    else:
        for i in sensor_number[0:2]:
            exec(f"instance.root.bind('<KeyPress-{i}>', lambda a: sensitivity_adjust_thread(sensor_area[{pressed_key}-1]+str({i})) )")
    return

def sensitivity_adjust(instance, selected_area):
    for i in sensor_number[0:6]:
        instance.root.unbind(f'<KeyPress-{i}>')

    prompt_image = Image.new("RGBA", (1080,1080))
    draw = ImageDraw.Draw(prompt_image)

    if selected_area != "g":
        draw.text((520,520), selected_area, font=sensor_titles_fontset[0])
        adjusts_value = get_sensor_sense_adjust(index=sensor_info.index(selected_area))
    else:
        draw.text((460,520), "Global", font=sensor_titles_fontset[0])
        adjusts_value = get_sensor_sense_adjust(index=selected_area)

    settings_prompt_position = list(area_title_position.values())[2:6]
    select_prompt_position = list(area_subtitl_position.values())[2:6]
    option_list = ["Back", "+", "-", "Apply"]

    for pos, setting in zip(settings_prompt_position, option_list):
        draw.text(pos, setting, font=sensor_titles_fontset[0])
    for pos, num in zip(select_prompt_position, sensor_number[2:6]):
        draw.text(pos, f"Press {num}", font=sensor_titles_fontset[1])

    prompt_image_edited = prompt_image.copy()
    draw = ImageDraw.Draw(prompt_image_edited)

    if adjusts_value != "0":
        draw.text((520,600), adjusts_value, font=sensor_titles_fontset[0])
    else:
        draw.text((530,600), adjusts_value, font=sensor_titles_fontset[0])

    prompt_image_edited = prompt_image_edited.resize((canvas_size,)*2)
    instance.edit_canvas.set_sensor_text(prompt_image_edited)

    instance.root.bind('<KeyPress-3>', lambda a: main(main_instance))
    instance.root.bind('<KeyPress-4>', lambda a: sensitivity_adjusting(main_instance, prompt_image, selected_area, "+", int(adjusts_value)))
    instance.root.bind('<KeyPress-5>', lambda a: sensitivity_adjusting(main_instance, prompt_image, selected_area, "-", int(adjusts_value)))
    instance.root.bind('<KeyPress-6>', lambda a: instance.reset_thread_draw_text())
    return

def sensitivity_adjust_thread(selected_area):
    threading.Thread(target=sensitivity_adjust, args=[main_instance, selected_area]).start()

def sensitivity_adjusting(instance, image, area, stat, value:int):
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
    instance.edit_canvas.set_sensor_text(prompt_image)

    instance.root.bind('<KeyPress-4>', lambda a: sensitivity_adjusting(main_instance, image, area, "+", value))
    instance.root.bind('<KeyPress-5>', lambda a: sensitivity_adjusting(main_instance, image, area, "-", value))
    instance.root.bind('<KeyPress-6>', lambda a: apply_sensitivity_settings(main_instance, area, value))
    return

def apply_sensitivity_settings(instance, area, value):
    for i in sensor_number[2:6]:
        instance.root.unbind(f'<KeyPress-{i}>')
    instance.stop_draw_touch.set()
    adjust_sense_reset(area)
    adjust_sense(area, value)
    instance.reset_thread_draw_text()
    instance.reset_thread_draw_touch()
    instance.done_execute_command("sense")
    return

if __name__ == "__main__":
    import tkinter as tk
    from PIL import ImageTk
    from communication import create_connection

    class Test:
        def __init__(self, root):
            self.root = root
            self.c = tk.Canvas(self.root, width=canvas_size, height=canvas_size, bg="black")
            self.c.pack()
            self.edit_canvas = EditSensorCanvas(self.c)
            main(self)
            root.mainloop()

    class EditSensorCanvas:
        def __init__(self, sensor_canvas):
            self.sensor_canvas = sensor_canvas

        def set_sensor_text(self, image):
            self.sensor_text_photoimage = ImageTk.PhotoImage(image)
            if self.sensor_canvas.find_withtag('text'):
                self.sensor_canvas.delete('text')
            self.sensor_canvas.create_image(canvas_size/2, canvas_size/2, image=self.sensor_text_photoimage, tag='text')

        def set_sensor_touch(self, imagelist):
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