from __future__ import annotations

import os
import queue
import sys
import threading
import time

import ttkbootstrap as tb
import screeninfo
from PIL import Image

import communication
import draw2 as draw
import preset_var
from features import buttons, system_buttons
from gui.dialogs import PortDialog
from gui.widgets import Card, FieldList, LogPanel, SensorView, StatusPill
from preset_var import BASIC_INFO_LABEL, IMAGES_DIR, PORT_LABELS, CONFIG_FILE

PUMP_MS = 20
TOUCH_INTERVAL = 0.01


class MainUI:
    def __init__(self, root: tb):
        self.root = root
        self._queue = queue.Queue()
        self._running = threading.Event()
        self._connected = False
        self._mode = "normal"
        self._fullscreen = False
        self._geometry_before_fullscreen = ""
        self._last_sensor_status = None
        self._closed = False
        self._log_visible = False
        self._log_job = None

        # kept for the feature screens that still toggle these names
        self.stop_draw_text = 0
        self.stop_draw_touch = 0

        self._build_header()
        self._build_info()
        self._build_actions()
        self._build_sensor()

        self.canvas = self.sensor        # features call this name

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.after(10, self._pump)
        self.log.info("Ready.")

    # ---------- layout ----------
    def _build_header(self):
        header = tb.Frame(self.root, padding=(16, 12, 16, 2))
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(2, weight=1)

        self.connect_btn = tb.Button(
            header, text="Connect", bootstyle="primary", width=13,
            command=self.connect_btn_clicked,
        )
        self.connect_btn.grid(row=0, column=0, sticky="w")

        self.status = StatusPill(header)
        self.status.grid(row=0, column=1, sticky="w", padx=(12, 0))

        self.log_btn = tb.Button(
            header, text="Log", bootstyle="secondary-outline", width=10,
            command=self.log_btn_clicked,
        )
        self.log_btn.grid(row=0, column=3, sticky="e", padx=(0, 8))

        self.full_btn = tb.Button(
            header, text="Fullscreen", bootstyle="secondary-outline", width=10,
            command=self.full_btn_clicked,
        )
        self.full_btn.grid(row=0, column=4, sticky="e")

    def _build_info(self):
        colors = self.root.style.colors
        self.info = tb.Frame(self.root, padding=(16, 8))
        self.info.grid(row=1, column=0, sticky="ew")
        self.info.columnconfigure(0, weight=1, uniform="info")
        self.info.columnconfigure(1, weight=1, uniform="info")

        left = Card(self.info, "Connection")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        self.ports_fields = FieldList(left, PORT_LABELS)
        self.ports_fields.grid(row=0, column=0, sticky="ew")

        tools = tb.Frame(left)
        tools.grid(row=1, column=0, sticky="w", pady=(10, 0))
        tools_buttons = [
            tb.Button(
                tools, text="static touch view", bootstyle="secondary-outline",
                command=self.static_touch_view_btn_clicked
            ),
            tb.Button(
                tools, text="led test", bootstyle="secondary-outline",
                command=self.led_test_btn_clicked
            )
        ]
        for i in tools_buttons:
            i.pack(side="left", padx=(0, 8))

        right = Card(self.info, "Device")
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        self.device_fields = FieldList(right, BASIC_INFO_LABEL)
        self.device_fields.grid(row=0, column=0, sticky="ew")

        system = tb.Frame(right)
        system.grid(row=1, column=0, sticky="w", pady=(10, 0))
        self._system_buttons = [
            tb.Button(
                system, text=name, bootstyle="secondary-outline",
                state="disabled", command=lambda n=name: self.execute_feature(n),
            )
            for name in system_buttons
        ]
        for i in self._system_buttons:
            i.pack(side="left", padx=(0, 8))

        # the log floats above the info cards until the Log button toggles it
        self.log = LogPanel(self.info, colors)

    def _build_actions(self):
        actions = tb.Frame(self.root, padding=(16, 4))
        actions.grid(row=2, column=0, sticky="ew")
        self._action_buttons = {}
        for b in buttons:
            self._action_buttons[b] = tb.Button(
                actions, text=b, state="disabled",
                command=lambda n=b: self.execute_feature(n),
            )
        for i, name in enumerate(self._action_buttons):
            self._action_buttons[name].grid(row=0, column=i, sticky="ew", padx=(6, 0))
            actions.columnconfigure(i, weight=1, uniform="action")

    def _build_sensor(self):
        base = Image.open(os.path.join(IMAGES_DIR, "sensor.png")).convert("RGBA")
        self.root.rowconfigure(3, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.sensor = SensorView(self.root, base)
        self.sensor.grid(row=3, column=0, sticky="nsew")

    # ---------- cross thread plumbing ----------
    def post(self, callback):
        if self._closed:
            return
        self._queue.put(callback)

    def _pump(self):
        while True:
            try:
                callback = self._queue.get_nowait()
            except queue.Empty:
                break
            try:
                callback()
            except Exception as exc:            # keep the pump alive
                self.log.error(f"UI update failed: {exc}")
        if not self._closed:
            self.root.after(10, self._pump)

    @staticmethod
    def _run(func, *args):
        threading.Thread(target=func, args=args, daemon=True).start()

    def on_close(self):
        """Stop the readers before the window goes away."""
        self._closed = True
        if self._log_job is not None:
            self.root.after_cancel(self._log_job)
            self._log_job = None
        self._stop_pollers()
        communication.disconnect()
        self.root.destroy()
        sys.exit()

    # ---------- connection ----------
    def connect_btn_clicked(self):
        if self._connected:
            self.disconnect()
        else:
            self.connect()

    def connect(self):
        cli_port = (CONFIG_FILE.get("cli_port") or "").strip()
        touch_port = (CONFIG_FILE.get("touch_port") or "").strip()
        if not cli_port or not touch_port:
            self.log.warn("No ports configured yet.")
            self.open_port_dialog()
            return
        self.status.set_state("connecting")
        self.connect_btn.configure(text="Connecting…", state="disabled")
        self._run(self._connect_worker, cli_port, touch_port)

    def _connect_worker(self, cli_port, touch_port):
        try:
            communication.connect(cli_port, touch_port)
            if not communication.touch.init_panel():
                raise communication.DeviceError("no status frame from the touch port")
            info = communication.cli.device_info()
        except communication.DeviceError as exc:
            communication.disconnect()
            self.post(lambda message=str(exc): self._connect_failed(message))
            return
        self.post(lambda: self._connect_done(cli_port, touch_port, info))

    def _connect_done(self, cli_port, touch_port, info):
        self._connected = True
        self.status.set_state("connected")
        self.connect_btn.configure(text="Disconnect", state="normal")
        self.ports_fields.set({
            "Command line": cli_port,
            "Touch": touch_port,
            "LED": CONFIG_FILE.get("led_port", ""),
            "Aime": CONFIG_FILE.get("aime_port", ""),
        })
        self._show_device_info(info)
        self.log.info(f"Connected to {cli_port} / {touch_port}.")
        self._set_enabled(True)
        self._start_pollers()

    def _connect_failed(self, message):
        self.status.set_state("disconnected")
        self.connect_btn.configure(text="Connect", state="normal")
        self.log.error(message)
        self.open_port_dialog()

    def disconnect(self):
        self._stop_pollers()
        communication.disconnect()
        self._connected = False
        self._mode = "normal"
        self.status.set_state("disconnected")
        self.connect_btn.configure(text="Connect", state="normal")
        self.ports_fields.clear()
        self.device_fields.clear()
        self.canvas.set_text(None)
        self.canvas.clear_touch()
        self._last_sensor_status = None
        self._set_enabled(False)
        self.log.info("Disconnected.")

    # ---------- pollers ----------
    def _start_pollers(self):
        self._stop_pollers()
        self._running.set()
        for target in (self._readings_loop, self._touch_loop):
            threading.Thread(target=target, daemon=True).start()

    def _stop_pollers(self):
        self._running.clear()

    def _readings_loop(self):
        interval = CONFIG_FILE.get("raw_readings_interval_time") or 0
        show_sense_adjust = CONFIG_FILE.get("always_show_sense_adjust", True)
        while self._running.is_set():
            if self._mode == "normal":
                try:
                    raw = communication.cli.raw_readings()
                    adjust = communication.cli.sense_adjust() if show_sense_adjust else None
                except communication.DeviceError as exc:
                    self.post(lambda error=str(exc): self._lost(error))
                    return
                # self.post(lambda readings=raw, values=adjust: self._show_readings(readings, values))
                self._show_readings(raw, adjust)
            if interval <= 0:
                return
            time.sleep(interval)

    def _touch_loop(self):
        while self._running.is_set():
            sensor_status = communication.touch.read_touch()
            if sensor_status:
                self._show_touch(sensor_status)
            # time.sleep(0.01)

    def _show_readings(self, readings: list[str], adjust: list[str] | None):
        self.canvas.set_text(draw.readings_image(readings, adjust))

    def _show_touch(self, status: list[int]):
        if status == self._last_sensor_status:
            return
        self._last_sensor_status = status
        self.canvas.set_touch(status)# draw.touch_image(status)

    def _lost(self, message):
        self._stop_pollers()
        communication.disconnect()
        self._connected = False
        self._mode = "normal"
        self.status.set_state("disconnected")
        self.connect_btn.configure(text="Connect", state="normal")
        self._set_enabled(False)
        self.log.error(f"Connection lost: {message}")

    def _show_device_info(self, info):
        self.device_fields.set({
            "SN": info.get("SN"),
            "Built": info.get("Built"),
            "Brightness": info.get("Brightness level"),
            "Global sensitivity": info.get("Global sensitivity"),
            "HID mode": info.get("HID mode"),
            "NFC module": info.get("NFC module"),
        })

    # ---------- feature screens ----------
    def execute_feature(self, name):
        action = buttons.get(name) or system_buttons.get(name)
        if action is None or not self._connected:
            return
        self._mode = "feature"
        self.canvas.clear_touch()
        self._last_sensor_status = None
        self.log.info(f"{name} opened.")
        for key in ("Left", "Right", "Up", "Down", "Return", "Insert", "End",
                    "BackSpace", "Backspace"):
            self.root.unbind(f"<KeyPress-{key}>")
        self.root.bind("<KeyPress-Escape>", lambda _event: self.done_command("esc"))
        action(self)

    def done_command(self, command="esc"):
        self._mode = "normal"
        self.root.unbind("<KeyPress-Escape>")
        self.root.unbind("<KeyPress-Backspace>")
        self.root.unbind("<KeyPress-BackSpace>")
        if not self._connected:
            return
        self.status.set_state("connected")
        self.refresh_readings()
        if command == "refresh":
            self.refresh_device_info()

    def refresh_readings(self):
        try:
            raw = communication.cli.raw_readings()
            adjust = communication.cli.sense_adjust()
        except communication.DeviceError as exc:
            self._lost(str(exc))
            return
        self._show_readings(raw, adjust)

    def refresh_device_info(self):
        try:
            info = communication.cli.device_info()
        except communication.DeviceError as exc:
            self._lost(str(exc))
            return
        self._show_device_info(info)

    # ---------- header actions ----------
    def log_btn_clicked(self):
        """Slide the log down over the info cards, or back up behind them."""
        if self._log_job is not None:
            self.root.after_cancel(self._log_job)
            self._log_job = None

        self._log_visible = not self._log_visible
        start, end = (-1.0, 0.0) if self._log_visible else (0.0, -1.0)
        begin = time.perf_counter()

        self.log.place(relx=0, rely=start, relwidth=1, relheight=1)
        self.log.lift()

        def step():
            progress = min(1.0, (time.perf_counter() - begin)*4)
            eased = 1 - (1 - progress) ** 3        # ease out: soft landing
            self.log.place_configure(rely=start + (end - start) * eased)
            if progress >= 1.0:
                self._log_job = None
            else:
                self._log_job = self.root.after(5, step)
            if not self._log_visible and progress >= 1.0:
                self.log.place_forget()

        step()      # draw the first frame right away instead of waiting 10 ms

    def full_btn_clicked(self):
        if self._fullscreen:
            self.root.overrideredirect(False)
            self.root.lift()
            self._fullscreen = False
            self.root.geometry(self._geometry_before_fullscreen)
        else:
            self._geometry_before_fullscreen = self.root.winfo_geometry()
            for mornitor in screeninfo.get_monitors():
                if (mornitor.x < self.root.winfo_rootx() + int(self.root.winfo_width() * 0.9) < mornitor.x + mornitor.width) \
                or (mornitor.y < self.root.winfo_rooty() + int(self.root.winfo_height() * 0.9) < mornitor.y + mornitor.height):
                    self.root.overrideredirect(True)
                    self.root.geometry(f"{mornitor.width}x{mornitor.height}+{mornitor.x}+{mornitor.y}")
                    self.root.lift()
                    self.root.focus_force()
                    self._fullscreen = True
                    break

    def not_implemented(self, name):
        self.log.warn(f"{name} is not implemented yet.")

    # ---------- feature buttons ----------
    def static_touch_view_btn_clicked(self):
        self.not_implemented("static touch view")

    def led_test_btn_clicked(self):
        self.not_implemented("led test")

    # ---------- ports ----------
    def open_port_dialog(self):
        PortDialog(self.root, CONFIG_FILE, self._save_ports)

    def _save_ports(self, values):
        preset_var.update_config(**values)
        CONFIG_FILE.update(values)
        self.ports_fields.set({
            "Command line": values.get("cli_port", ""),
            "Touch": values.get("touch_port", ""),
            "LED": values.get("led_port", ""),
            "Aime": values.get("aime_port", ""),
        })
        self.log.info("Ports saved to config.yaml.")

    def _set_enabled(self, enabled):
        state = "normal" if enabled else "disabled"
        for button in list(self._action_buttons.values()) + self._system_buttons:
            button.configure(state=state)
