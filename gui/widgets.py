"""Reusable widgets for the main window."""

from __future__ import annotations

import time
import tkinter as tk

import ttkbootstrap as tb
from PIL import Image, ImageTk

from preset_var import SENSOR_INFO
import draw2 as draw


class Card(tb.Labelframe):
    """
    A titled container that follows the active theme.
    """

    def __init__(self, parent, title: str, **kwargs):
        super().__init__(parent, text=title, padding=12, **kwargs)


class FieldList(tb.Frame):
    """
    A two column list of label/value rows.
    """

    def __init__(self, parent, fields):
        super().__init__(parent)
        self._values = {}
        for row, name in enumerate(fields):
            tb.Label(self, text=name).grid(row=row, column=0, sticky="w", pady=3)
            value = tk.StringVar(value="—")
            tb.Label(self, textvariable=value, bootstyle="secondary").grid(
                row=row, column=1, sticky="w", padx=(16, 0), pady=3
            )
            self._values[name] = value
        self.columnconfigure(1, weight=1)

    def set(self, values: dict) -> None:
        for name, value in values.items():
            if name in self._values:
                self._values[name].set(str(value) if value else "—")

    def clear(self) -> None:
        for value in self._values.values():
            value.set("—")


class StatusPill(tb.Label):
    """
    Connection state, shown with a coloured label.
    """

    STATES = {
        "disconnected": ("Disconnected", "secondary.TLabel"),
        "connecting": ("Connecting…", "warning.TLabel"),
        "connected": ("Connected", "success.TLabel"),
        "busy": ("Busy", "info.TLabel"),
    }

    def __init__(self, parent):
        super().__init__(parent, text="Disconnected", bootstyle="secondary")
        self.set_state("disconnected")

    def set_state(self, state: str) -> None:
        text, style = self.STATES.get(state, self.STATES["disconnected"])
        self.configure(text=text, style=style)


class LogPanel(tb.Frame):
    """
    Read only log with a coloured level prefix per line.
    """

    def __init__(self, parent, colors):
        super().__init__(parent)
        self._text = tb.Text(
            self,
            height=6,
            wrap="word",
            relief="solid",
            borderwidth=1,
            padx=10,
            pady=8,
            autostyle=False,
            insertbackground=colors.fg,
            selectbackground=colors.selectbg,
            selectforeground=colors.selectfg,
        )
        scroll = tb.Scrollbar(self, orient="vertical", command=self._text.yview)
        self._text.configure(yscrollcommand=scroll.set)
        self._text.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self._text.tag_configure("warn", foreground=colors.warning)
        self._text.tag_configure("error", foreground=colors.danger)
        self._text.tag_configure("time", foreground=colors.secondary)
        self._text.configure(state="disabled")

    def _write(self, level: str, message: str, tag: str) -> None:
        stamp = time.strftime("%H:%M:%S")
        self._text.configure(state="normal")
        self._text.insert("end", f"{stamp} ", "time")
        self._text.insert("end", f"[{level}] {message}\n", tag)
        self._text.see("end")
        self._text.configure(state="disabled")

    def info(self, message: str) -> None:
        self._write("INF", message, "")

    def warn(self, message: str) -> None:
        self._write("WRN", message, "warn")

    def error(self, message: str) -> None:
        self._write("ERR", message, "error")

    def clear(self) -> None:
        self._text.configure(state="normal")
        self._text.delete("1.0", "end")
        self._text.configure(state="disabled")


class SensorView(tb.Frame):
    """
    Layered sensor view: base art, touch overlay and text, scaled to fit.

    All three layers are 1080x1080 RGBA images. The art is kept square, sized
    to the smaller side of this widget, centred horizontally and pinned to the
    bottom, so widening the window makes the sensor grow.
    """

    def __init__(self, parent, base_image: Image.Image):
        super().__init__(parent)
        self._canvas = tb.Canvas(self)
        self._canvas.pack(fill="both", expand=True)
        self._layers = {"base": base_image, "text": None}
        self._photoimage = {"base": None, "text": None}
        self._active_list = None
        self._size = 0
        self._job = None
        self._canvas.bind("<Configure>", self._on_configure)

    # ---------- public ----------
    def set_text(self, image: Image.Image) -> None:
        self._layers["text"] = image
        self._draw("text")

    def set_touch(self, active_list: list[int]) -> None:
        if active_list is None:
            return
        self._active_list = active_list
        for index, sensor in enumerate(SENSOR_INFO):
            self._canvas.itemconfigure(sensor, state="normal" if active_list[index] else "hidden")

    def clear_touch(self) -> None:
        self.set_touch(None)

    # ---------- internals ----------
    def _on_configure(self, _event) -> None:
        if self._job is not None:
            self.after_cancel(self._job)
            self._job = None
        self._job = self.after(10, self._rescale)

    def _rescale(self) -> None:
        self._job = None
        size = min(self._canvas.winfo_width(), self._canvas.winfo_height())
        self._size = size
        self._draw("base")
        self._build_touch_area_layers()
        self._draw("text")

    def _draw(self, tag: str) -> None:
        items = self._canvas.find_withtag(tag)
        image = self._layers.get(tag)

        if image is None or not self._size:
            for item in items:
                self._canvas.itemconfigure(item, state="hidden")
            return

        self._photoimage[tag] = ImageTk.PhotoImage(
            image.resize((self._size, self._size), Image.BILINEAR)
        )
        x = self._canvas.winfo_width() / 2                # centred
        y = self._canvas.winfo_height() - self._size / 2  # pinned to the bottom

        if items:
            self._canvas.coords(items[0], x, y)
            self._canvas.itemconfigure(
                items[0], image=self._photoimage[tag], state="normal"
            )
        else:
            self._canvas.create_image(x, y, image=self._photoimage[tag], tags=tag)

        self._canvas.tag_raise("text")

    def _build_touch_area_layers(self) -> None:
        """
        Rebuild the 34 cropped highlight items for the current size.
        """
        self._canvas.delete("touch")
        scale = self._size / draw.CANVAS_SIZE
        space_from_left = (self._canvas.winfo_width() - self._size) / 2
        space_from_top = self._canvas.winfo_height() - self._size

        for index, sensor in enumerate(SENSOR_INFO):
            box = draw.AREA_TOUCH_BBOX[index]
            x0, y0, x1, y1 = box
            self._photoimage[sensor] = ImageTk.PhotoImage(
                draw.AREA_TOUCH_LAYER[index].crop(box).resize(
                    (int((x1 - x0) * scale), int((y1 - y0) * scale)),
                    Image.BILINEAR,
                )
            )
            self._canvas.create_image(
                space_from_left + (x0 + x1) / 2 * scale,
                space_from_top + (y0 + y1) / 2 * scale,
                image=self._photoimage[sensor],
                state="hidden",
                tags=("touch", sensor),
            )

        self._canvas.tag_raise("text")
        self.set_touch(self._active_list)