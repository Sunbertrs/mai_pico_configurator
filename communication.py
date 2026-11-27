"""
The command port is driven by a single worker thread: callers hand it a request
and wait for the answer, so two threads can never interleave on the wire.
The touch port keeps a lock of its own, since its frames are polled directly.
"""

from __future__ import annotations

import queue
import re
import threading
import time
from contextlib import contextmanager

import serial

from preset_var import config_get, sensor_area

IDLE_TIMEOUT = 0.08
TOUCH_FRAME = 9


class DeviceError(RuntimeError):
    """A serial operation could not be completed."""


class PortBusy(DeviceError):
    """The request did not finish in time; the caller may retry."""


class SerialPort:
    """
    One serial port: connection state, a reentrant lock and error mapping.
    """

    def __init__(self, label: str):
        self.label = label
        self.port_name = ""
        self._lock = threading.RLock()
        self._serial = None

    def open(self, port_name: str) -> None:
        with self.exclusive():
            self._close_locked()
            try:
                self._serial = serial.Serial(port_name, timeout=0.02)
            except (serial.SerialException, OSError) as exc:
                print(exc)
                raise DeviceError(f"cannot open {port_name} ({self.label}): {exc}") from exc
            self.port_name = port_name

    def close(self) -> None:
        with self.exclusive():
            self._close_locked()

    def is_open(self) -> bool:
        return self._serial is not None and self._serial.is_open

    @contextmanager
    def exclusive(self):
        """
        Hold the port lock; give up with DeviceError instead of waiting forever.
        """
        if not self._lock.acquire(timeout=5.0):
            raise DeviceError(f"{self.label} is busy")
        try:
            yield self
        finally:
            self._lock.release()

    def _close_locked(self) -> None:
        try:
            if self._serial is not None and self._serial.is_open:
                self._serial.close()
        except (serial.SerialException, OSError):
            pass
        self._serial = None

    def _require_port(self):
        if self._serial is None or not self._serial.is_open:
            raise DeviceError(f"{self.label} is not open")
        return self._serial


class _Request:
    """
    One queued command and the slot its answer lands in.
    """

    __slots__ = ("command", "event", "lines", "error", "cancelled")

    def __init__(self, command: str):
        self.command = command
        self.event = threading.Event()
        self.lines: list[str] = []
        self.error: DeviceError | None = None
        self.cancelled = False


class CliPort(SerialPort):
    """
    The command console, served by one worker thread.

    Callers enqueue a request and wait on its event, so the port has exactly one
    reader at a time and there is no lock that can time out as "busy".
    """

    def __init__(self):
        super().__init__("command port")
        self._queue: queue.Queue = queue.Queue()
        self._stop = threading.Event()
        self._worker: threading.Thread | None = None

    # ---------- lifecycle ----------
    def open(self, port_name: str) -> None:
        self.close()
        try:
            self._serial = serial.Serial(port_name, timeout=0.02)
        except (serial.SerialException, OSError) as exc:
            raise DeviceError(f"cannot open {port_name} ({self.label}): {exc}") from exc
        self.port_name = port_name
        self._queue = queue.Queue()
        self._stop = threading.Event()
        self._worker = threading.Thread(
            target=self._serve, args=(self._queue, self._stop), daemon=True
        )
        self._worker.start()

    def close(self) -> None:
        worker, self._worker = self._worker, None
        stop, self._stop = self._stop, None
        if stop is not None:
            stop.set()
        if worker is not None:
            self._queue.put(None)          # wake the worker out of get()
        self._close_serial()               # unblocks a read in progress
        if worker is not None and worker.is_alive():
            worker.join(0.5)

    def _close_serial(self) -> None:
        if self._serial is not None:
            try:
                self._serial.close()
            except (serial.SerialException, OSError):
                pass
            self._serial = None

    # ---------- worker ----------
    def _serve(self, requests: queue.Queue, stop: threading.Event) -> None:
        while not stop.is_set():
            request = requests.get()
            if request is None:
                return
            if request.cancelled:
                request.event.set()
                continue
            try:
                request.lines = self._exchange(request.command)
            except DeviceError as exc:
                request.error = exc
            request.event.set()

    def _exchange(self, command: str) -> list[str]:
        port = self._serial
        if port is None or not port.is_open:
            raise DeviceError(f"{self.label} is not open")
        try:
            port.reset_input_buffer()
            port.write(command.encode())
        except (serial.SerialException, OSError) as exc:
            raise DeviceError(f"write failed: {exc}") from exc
        return self._read_lines(port)

    # ---------- low level ----------
    def submit(self, command: str, timeout: float = 5.0) -> list[str]:
        """
        Send one command and wait for the reply lines.
        """
        if self._worker is None:
            raise DeviceError(f"{self.label} is not open")
        request = _Request(command)
        self._queue.put(request)
        if not request.event.wait(timeout):
            request.cancelled = True
            raise PortBusy(f"{self.label} is busy")
        if request.error is not None:
            raise request.error
        return request.lines

    @staticmethod
    def _read_lines(port) -> list[str]:
        """
        Read until the prompt shows up, or until the line stream goes quiet.
        """
        lines = []
        deadline = time.monotonic() + 1.0
        last_data = time.monotonic()
        while time.monotonic() < deadline:
            if lines and time.monotonic() - last_data > IDLE_TIMEOUT:
                break
            try:
                raw = port.readline()
            except (serial.SerialException, OSError) as exc:
                raise DeviceError(f"read failed: {exc}") from exc
            if not raw:
                continue
            text = raw.decode().strip()
            if text.endswith("mai_pico>"):
                break
            lines.append(text)
            last_data = time.monotonic()
        return lines

    # ---------- display parsing ----------
    @staticmethod
    def parse_sections(lines: list[str]) -> dict[str, list[str]]:
        """
        Split a `display` reply into sections.

        A section starts at a line like "[HID]" and runs until the next such
        line, so the result maps "HID" to the lines below it.
        """
        sections = {}
        current = None
        for line in lines:
            text = line.strip()
            if text.startswith("[") and text.endswith("]"):
                current = sections.setdefault(text[1:-1], [])
            elif current is not None and text:
                current.append(text)
        return sections

    @staticmethod
    def _after_colon(line: str) -> str:
        """Text after the first colon: "Level: 127" -> "127"."""
        return line.split(":", 1)[1].strip() if ":" in line else ""

    @classmethod
    def _section_value(cls, lines, prefix: str, default: str = "N/A") -> str:
        for line in lines:
            if line.lower().startswith(prefix.lower()):
                value = cls._after_colon(line)
                return value if value else default
        return default

    @classmethod
    def _rgb_level(cls, sections) -> str:
        return cls._section_value(sections.get("RGB", []), "Level")

    @classmethod
    def _sense_value(cls, sections, index=None):
        sense = sections.get("Sense", [])
        if index == "g":
            for line in sense:
                if "global" in line.lower():
                    # The line reads "Sensitivity (global: +1):", so keep only
                    # the sign and the digits to end up with "+1".
                    value = re.sub(r"[^+\-0-9]", "", line)
                    return "0" if value in ("", "+0", "-0") else value
            return "0"
        grid = []
        for line in sense:
            if line[:1] in sensor_area and "|" in line:
                grid.extend(part.strip() for part in line.split("|")[1:-1])
        if not grid:
            return [] if index is None else "0"
        adjusted = []
        for value in grid:
            try:
                number = int(value)
            except ValueError:
                adjusted.append("0")
                continue
            if number == 0:
                adjusted.append("0")
            elif number < 128:
                adjusted.append(f"+{number}")
            else:
                adjusted.append(f"-{256 - number}")
        if index is None:
            return adjusted
        try:
            return adjusted[int(index)]
        except (ValueError, IndexError):
            return "0"

    @staticmethod
    def _hid(sections, ignore_stuck=None) -> str:
        hid = sections.get("HID", [])
        if not hid:
            return "unknown"
        first = hid[0].lower()
        if "joy: on" in first or "io4: on" in first:
            mode = "io4"
        elif "nkro" in first:
            # "Joy: off, NKRO: key1" -> "key1"
            mode = first.split("nkro", 1)[1].lstrip(":").strip()
        else:
            mode = "unknown"
        if len(hid) > 1 and hid[1].startswith("!!!") and not ignore_stuck:
            mode += "!"
        return mode

    @classmethod
    def _aime_fields(cls, sections) -> dict:
        aime = sections.get("AIME", [])
        return {
            "NFC Module": cls._section_value(aime, "NFC Module"),
            "Virtual AIC": cls._section_value(aime, "Virtual AIC"),
            "Protocol Mode": cls._section_value(aime, "Protocol Mode"),
        }

    @staticmethod
    def _parse_gpio_line(line: str) -> list[str]:
        """Turn "Main: 1, 0, 4" or "Main: GP1 GP0 GP4" into ["GP1", "GP0", "GP4"]."""
        body = line.split(":", 1)[1] if ":" in line else line
        values = []
        for token in body.replace(",", " ").split():
            if token.upper().startswith("GP"):
                token = token[2:]
            if token.isdigit():
                values.append(f"GP{token}")
        return values

    @classmethod
    def _gpio_rows(cls, sections) -> list[list[str]]:
        return [cls._parse_gpio_line(line) for line in sections.get("GPIO", [])]

    @staticmethod
    def _is_unsupported(lines) -> bool:
        return any("unknown command" in line.lower() for line in lines)

    # ---------- reads ----------
    def read_display(self) -> dict:
        return self.parse_sections(self.submit("display\n"))

    def device_info(self) -> dict:
        """One round trip for the header panel."""
        info = {"SN": "N/A", "Built": "N/A"}
        header = self.submit("?\n")
        for line in header:
            key = line.partition(":")[0].strip()
            if key in info:
                info[key] = self._after_colon(line) or "N/A"
        sections = self.read_display()
        info["Brightness level"] = self._rgb_level(sections)
        info["Global sensitivity"] = self._sense_value(sections, "g")
        info["HID mode"] = self._hid(sections)
        info["NFC module"] = self._aime_fields(sections)["NFC Module"]
        return info

    def basic_info(self) -> list:
        """Same six values as before, in the same order."""
        info = self.device_info()
        return [
            info["SN"],
            info["Built"],
            info["Brightness level"],
            info["Global sensitivity"],
            info["HID mode"],
            info["NFC module"],
        ]

    def raw_readings(self) -> list[str]:
        readings = []
        for line in self.submit("raw\n"):
            text = line.strip()
            if text[:1] in sensor_area and "|" in text:
                readings.extend(part.strip() for part in text.split("|")[1:-1])
        return readings

    def sense_adjust(self, index=None):
        return self._sense_value(self.read_display(), index)

    def brightness_level(self) -> str:
        return self._rgb_level(self.read_display())

    def hid_mode(self, ignore_stuck=None) -> str:
        return self._hid(self.read_display(), ignore_stuck)

    def hid_off_available(self) -> int:
        for line in self.submit("hid\n"):
            if "off" in line.lower():
                return 1
        return 0

    def naming_joy(self) -> bool:
        hid = self.read_display().get("HID", [])
        return bool(hid) and "joy" in hid[0].lower()

    def aime_info(self, more=None):
        if self._is_unsupported(self.submit("aime\n")):
            return "Unsupported"
        fields = self._aime_fields(self.read_display())
        if not more:
            return fields["NFC Module"]
        return (fields["Virtual AIC"], fields["Protocol Mode"])

    def gpio_info(self, aux=None):
        if self._is_unsupported(self.submit("gpio\n")):
            return "Unsupported"
        rows = self._gpio_rows(self.read_display())
        row = 1 if aux else 0
        return rows[row] if len(rows) > row else []

    # ---------- commands ----------
    def sense_reset(self, area) -> None:
        command = "sense 0\n" if area == "g" else f"sense {area} 0\n"
        self.submit(command)

    def adjust_sense(self, area: str, value: int) -> None:
        """Apply a relative sensitivity change; the whole sequence is atomic."""
        step = "+" if value > 0 else "-"
        with self.exclusive():
            for _ in range(abs(value)):
                if area == "g":
                    self.submit(f"sense {step}\n")
                else:
                    self.submit(f"sense {area} {step}\n")

    def set_hid_mode(self, mode) -> None:
        if mode == "io4" and self.naming_joy():
            mode = "joy"
        self.submit(f"hid {mode}\n")

    def set_aime_virtual_aic(self, value) -> None:
        self.submit(f"aime virtual {value.lower()}\n")

    def set_aime_protocol_mode(self, value) -> None:
        self.submit(f"aime mode {value}\n")

    def set_brightness(self, value) -> None:
        self.submit(f"level {value}\n")

    def set_gpio(self, kind, definition) -> None:
        if kind == "main":
            self.submit(f"gpio main {definition}\n")
        elif kind == "aux":
            self.submit(f"gpio {definition}\n")

    def gpio_reset(self) -> None:
        self.submit("gpio reset\n")

    def factory_reset(self) -> None:
        self.submit("factory\n")

    def update_firmware(self) -> None:
        """Ask the device to reboot into its firmware disk; the port disappears."""
        try:
            self.submit("update\n")
        except DeviceError:
            pass


class TouchPort(SerialPort):
    def __init__(self):
        super().__init__("touch port")

    def write(self, data: bytes) -> None:
        with self.exclusive():
            port = self._require_port()
            try:
                port.write(data)
            except (serial.SerialException, OSError) as exc:
                raise DeviceError(f"touch write failed: {exc}") from exc

    def flush(self) -> None:
        with self.exclusive():
            port = self._serial
            if port is not None and port.is_open:
                try:
                    port.reset_input_buffer()
                except (serial.SerialException, OSError):
                    pass

    def read_frame(self, timeout: float = 0.05) -> bytes:
        """
        Return one whole frame, or b"" when nothing arrived in time.
        """
        with self.exclusive():
            port = self._serial
            if port is None or not port.is_open:
                return b""
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                if port.in_waiting < TOUCH_FRAME:
                    time.sleep(0.002)
                    continue
                try:
                    resp = port.read(port.in_waiting)
                    if (resp[-9] != b"("[0]) and (resp[-1] != b")"[0]):
                        continue
                    return resp[-9:]
                except (serial.SerialException, OSError):
                    return b""
            return b""

    def init_panel(self) -> bool:
        """Configure the panel and wait for the first status frame."""
        # Thanks to @CVSJason(Github) for the reference on touch port communication implementation
        try:
            self.write(b"{RSET}")
            self.write(b"{HALT}")
            self.write(b"{LAr2}")
            for area in range(0x41, 0x63):
                self.write(b"{L" + bytes([area]) + b"r" + bytes([0x32]) + b"}")
            for area in range(0x41, 0x63):
                self.write(b"{L" + bytes([area]) + b"k" + bytes([0x28]) + b"}")
            self.write(b"{STAT}")
            self.flush()
            self.read_frame(timeout=1.0)
        except DeviceError:
            return False
        return True

    def read_touch(self) -> list[int]:
        """Return 34 touch flags, or [] when no frame is ready."""
        frame = self.read_frame()
        bits = []
        for byte in frame[1:]:
            for bit in range(5):
                bits.append(1 if byte & (1 << bit) else 0)
        return bits[:34]

    def stop(self) -> None:
        try:
            self.write(b"{RSET}")
            self.write(b"{HALT}")
        except DeviceError:
            pass


cli = CliPort()
touch = TouchPort()


def connect(cli_port: str, touch_port: str) -> None:
    """Open both ports; if the touch port fails, the command port is closed again."""
    cli.open(cli_port)
    try:
        touch.open(touch_port)
    except DeviceError:
        cli.close()
        raise


def disconnect() -> None:
    touch.close()
    cli.close()


def is_connected() -> bool:
    return cli.is_open()


def combine_raw_and_sense_adjust(raw, adjust) -> list[str]:
    """Merge readings and adjustments for display; not port related."""
    merged = list(raw)
    for index, value in enumerate(adjust):
        if value != "0" and index < len(merged):
            merged[index] = f"{merged[index]}({value})"
    return merged

def get_hardware_basic_info(): return cli.basic_info()
def get_sensor_raw_readings(): return cli.raw_readings()
def get_sensor_sense_adjust(index=None): return cli.sense_adjust(index)
def get_brightness_level(): return cli.brightness_level()
def get_hid_mode(ignore_stuck=None): return cli.hid_mode(ignore_stuck)
def get_hid_off_mode_availability(): return cli.hid_off_available()
def get_naming_joy(): return cli.naming_joy()
def get_aime_info(more=None): return cli.aime_info(more)
def get_gpio_info(aux=None): return cli.gpio_info(aux)
def adjust_sense_reset(area): return cli.sense_reset(area)
def adjust_sense(area, value): return cli.adjust_sense(area, value)
def adjust_hid_mode(mode): return cli.set_hid_mode(mode)
def adjust_aime_virtual_aic(value): return cli.set_aime_virtual_aic(value)
def adjust_aime_protocol_mode(value): return cli.set_aime_protocol_mode(value)
def adjust_brightness_level(value): return cli.set_brightness(value)
def adjust_gpio_buttons(kind, definition): return cli.set_gpio(kind, definition)
def gpio_reset(): return cli.gpio_reset()
def factory_reset(): return cli.factory_reset()
def program_update(): return cli.update_firmware()
def init_sensor_touch(): return touch.init_panel()
def get_sensor_touch(): return touch.read_touch()
def stop_get_touch_info(): return touch.stop()

cli_port = ""
touch_port = ""


def check_connect():
    conf_cli = config_get("cli_port", "")
    conf_touch = config_get("touch_port", "")
    if not conf_cli or not conf_touch:
        return ("Not_set",)
    probe_cli, probe_touch = CliPort(), TouchPort()
    try:
        probe_cli.open(conf_cli)
        probe_touch.open(conf_touch)
    except DeviceError as exc:
        return (0, str(exc))
    finally:
        probe_cli.close()
        probe_touch.close()
    return (1,)


def create_connection():
    global cli_port, touch_port
    cli_port = config_get("cli_port", "")
    touch_port = config_get("touch_port", "")
    connect(cli_port, touch_port)
