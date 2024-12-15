import tkinter as tk
from PIL import ImageTk, Image

from communication import create_connection
from preset_var import canvas_size
from cmds.hid import main

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
        self.sensor_canvas.create_image(canvas_size / 2, canvas_size / 2, image=self.sensor_text_photoimage,
                                        tag='text')

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
        sensor_touch_stat = Image.new('RGBA', (canvas_size,) * 2)
        for i in imagelist:
            sensor_touch_stat.paste(i, (0, 0), i)
        self.sensor_touch_photoimage = ImageTk.PhotoImage(sensor_touch_stat)
        self.sensor_canvas.create_image(canvas_size / 2, canvas_size / 2, image=self.sensor_touch_photoimage,
                                        tag="touch")
        self.sensor_canvas.tag_raise("text")

        self.sensor_touch_prev = imagelist

# create_connection()
a = Test(tk.Tk())