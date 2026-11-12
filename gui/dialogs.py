"""Port selection dialog."""

from __future__ import annotations

import ttkbootstrap as tb
from ttkbootstrap.dialogs import Messagebox

import port_name_detector
from preset_var import message_box_prompts, setting_port_manually_text

FIELDS = (
    ("Command line", "cli_port"),
    ("Touch", "touch_port"),
    ("LED", "led_port"),
    ("Aime", "aime_port"),
)


class PortDialog(tb.Toplevel):
    """Pick the serial ports; detected mai_pico ports are offered first."""

    def __init__(self, parent, config: dict, on_save):
        super().__init__(parent)
        self.title(setting_port_manually_text[0])
        self.resizable(False, False)
        self._config = config
        self._on_save = on_save

        tb.Label(self, text=setting_port_manually_text[1]).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=14, pady=(14, 6)
        )

        self._boxes = {}
        for row, (label, key) in enumerate(FIELDS, start=1):
            tb.Label(self, text=label).grid(row=row, column=0, sticky="w", padx=14, pady=6)
            box = tb.Combobox(self, width=36, state="readonly")
            box.grid(row=row, column=1, padx=14, pady=6)
            self._boxes[key] = box

        buttons = tb.Frame(self)
        buttons.grid(row=len(FIELDS) + 1, column=0, columnspan=2, sticky="e", padx=14, pady=14)
        tb.Button(buttons, text="Rescan", bootstyle="secondary-outline",
                  command=self._scan).pack(side="left", padx=(0, 8))
        tb.Button(buttons, text="Cancel", bootstyle="secondary",
                  command=self.destroy).pack(side="left", padx=(0, 8))
        tb.Button(buttons, text="OK", bootstyle="primary",
                  command=self._apply).pack(side="left")

        self._choices = []
        self._scan()

    def _scan(self) -> None:
        ports = port_name_detector.detect_ports(refresh=True)
        self._choices = [f"{com}  {name}" for com, name in ports.items()]
        for key, box in self._boxes.items():
            box["values"] = self._choices
            current = self._config.get(key, "") or ""
            match = next((item for item in self._choices if item.startswith(current)), "")
            box.set(match or (self._choices[0] if self._choices else ""))

    def _apply(self) -> None:
        values = {}
        for key, box in self._boxes.items():
            choice = box.get().strip()
            values[key] = choice.split()[0] if choice else ""

        chosen = [port for port in values.values() if port]
        if len(chosen) != len(set(chosen)):
            Messagebox.show_warning(
                message_box_prompts["Manual_port_repeat"][1],
                title=message_box_prompts["Manual_port_repeat"][0],
                parent=self,
            )
            return

        self._on_save(values)
        self.destroy()
