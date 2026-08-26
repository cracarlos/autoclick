import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Controller as KeyboardController, Key


def parse_key_spec(spec: str):
    spec = spec.strip().lower().replace(" ", "")
    if not spec:
        raise ValueError("Tecla vacía")

    parts = spec.split("+")
    mods = {"ctrl": Key.ctrl, "control": Key.ctrl, "alt": Key.alt,
            "shift": Key.shift, "cmd": Key.cmd, "win": Key.cmd, "meta": Key.cmd}
    special = {
        "enter": Key.enter, "return": Key.enter, "esc": Key.esc, "escape": Key.esc,
        "tab": Key.tab, "space": Key.space, "backspace": Key.backspace,
        "delete": Key.delete, "insert": "insert", "home": Key.home, "end": Key.end,
        "page_up": Key.page_up, "page_down": Key.page_down, "up": Key.up,
        "down": Key.down, "left": Key.left, "right": Key.right,
        "caps_lock": Key.caps_lock,
    }

    held = []
    key = None
    for part in parts:
        if part in mods:
            held.append(mods[part])
        elif part in special:
            key = special[part]
        elif part in ("f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10",
                      "f11", "f12", "f13", "f14", "f15", "f16", "f17", "f18", "f19", "f20"):
            key = getattr(Key, part)
        elif len(part) == 1:
            key = part
        else:
            mapped = getattr(Key, part, None)
            if mapped is None:
                raise ValueError(f"Tecla no reconocida: {part}")
            key = mapped

    if key is None:
        key = parts[-1]
        if len(key) != 1:
            raise ValueError(f"Tecla no reconocida: {key}")

    return held, key


def parse_sequence(spec: str) -> list:
    return [parse_key_spec(item) for item in spec.split(",") if item.strip()]


@dataclass
class ClickConfig:
    interval_ms: int = 100
    mode: str = "current"
    x: int = 0
    y: int = 0
    button: str = "left"
    double: bool = False
    repeat: int = 0
    on_status: Optional[Callable[[str], None]] = None
    _mouse: MouseController = field(default_factory=MouseController, repr=False)


@dataclass
class KeyboardConfig:
    sequence: str = ""
    interval_ms: int = 500
    repeat: int = 0
    on_status: Optional[Callable[[str], None]] = None
    _keyboard: KeyboardController = field(default_factory=KeyboardController, repr=False)


class ClickWorker:
    def __init__(self, config: ClickConfig):
        self.config = config
        self._stop = threading.Event()
        self._thread = None
        self.running = False

    def start(self):
        if self.running:
            return
        self._stop.clear()
        self.running = True
        self._thread = threading.Thread(target=self._run, name="click-worker", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        self.running = False
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None

    def is_running(self) -> bool:
        return self.running

    def _click(self):
        mouse = self.config._mouse
        if self.config.mode == "fixed":
            mouse.position = (self.config.x, self.config.y)

        button = getattr(Button, self.config.button, Button.left)
        if self.config.double:
            mouse.click(button, 2)
        else:
            mouse.click(button, 1)

    def _run(self):
        interval = self.config.interval_ms / 1000.0
        count = 0
        if self.config.on_status:
            self.config.on_status("click RUNNING")
        try:
            while not self._stop.wait(interval):
                self._click()
                count += 1
                if self.config.repeat > 0 and count >= self.config.repeat:
                    break
        finally:
            self.running = False
            if self.config.on_status:
                self.config.on_status("click STOPPED")


class KeyboardWorker:
    def __init__(self, config: KeyboardConfig):
        self.config = config
        self._stop = threading.Event()
        self._thread = None
        self.running = False

    def start(self):
        if self.running:
            return
        try:
            self._sequence = parse_sequence(self.config.sequence)
        except ValueError as exc:
            if self.config.on_status:
                self.config.on_status(f"error: {exc}")
            return
        self._stop.clear()
        self.running = True
        self._thread = threading.Thread(target=self._run, name="keyboard-worker", daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        self.running = False
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None

    def is_running(self) -> bool:
        return self.running

    def _press(self, held, key):
        kb = self.config._keyboard
        for k in held:
            kb.press(k)
        if isinstance(key, Key):
            kb.press(key)
            kb.release(key)
        else:
            kb.press(key)
            kb.release(key)
        for k in reversed(held):
            kb.release(k)

    def _run(self):
        interval = self.config.interval_ms / 1000.0
        count = 0
        if self.config.on_status:
            self.config.on_status("keyboard RUNNING")
        try:
            while not self._stop.wait(interval):
                for held, key in self._sequence:
                    if self._stop.is_set():
                        return
                    self._press(held, key)
                    time.sleep(0.02)
                count += 1
                if self.config.repeat > 0 and count >= self.config.repeat:
                    break
        finally:
            self.running = False
            if self.config.on_status:
                self.config.on_status("keyboard STOPPED")