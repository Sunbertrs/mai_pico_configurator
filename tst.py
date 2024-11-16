from tkinter import *
from PIL import ImageTk, Image

canvas_size = 500

class Test:
    def __init__(self, root):
        self.root = root
        self.sensor_canvas = Canvas(self.root, width=canvas_size, height=canvas_size, background='grey')
        self.sensor_canvas.pack()
        self.SENSOR_PIC = ImageTk.PhotoImage(Image.open("images/sensor.png").resize((canvas_size,)*2))
        self.sensor_canvas.create_image(canvas_size/2, canvas_size/2, image=self.SENSOR_PIC)
        self.btn = Button(self.root, text="Change", command=self.change)
        self.btn.pack()

    def change(self):
        self.SENSOR_PIC = ImageTk.PhotoImage(Image.open("images/bluesensor.png").resize((canvas_size,)*2))
        self.sensor_canvas.delete()
        self.sensor_canvas.create_image(canvas_size/2, canvas_size/2, image=self.SENSOR_PIC)

# import tkinter as tk
#

a = Tk()
Test(a)

a.mainloop()
