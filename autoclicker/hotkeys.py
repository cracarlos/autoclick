from pynput import keyboard


class HotkeyManager:
    def __init__(self, on_toggle_click, on_toggle_keyboard, on_capture):
        self._on_toggle_click = on_toggle_click
        self._on_toggle_keyboard = on_toggle_keyboard
        self._on_capture = on_capture
        self.recorder = None
        self._listener = None
        self._started = False

    def set_recorder(self, recorder):
        self.recorder = recorder

    def start(self):
        if self._started:
            return
        self._started = True
        self._listener = keyboard.Listener(
            on_press=self._on_press, on_release=self._on_release)
        self._listener.daemon = True
        self._listener.start()

    def stop(self):
        if self._listener:
            self._listener.stop()
            self._listener = None
        self._started = False

    def _on_press(self, key):
        if self.recorder is not None and self.recorder.recording:
            self.recorder.handle_press(key)
            return
        if key == keyboard.Key.f6:
            self._on_toggle_click()
        elif key == keyboard.Key.f7:
            self._on_toggle_keyboard()
        elif key == keyboard.Key.f8:
            self._on_capture()

    def _on_release(self, key):
        if self.recorder is not None and self.recorder.recording:
            self.recorder.handle_release(key)


class KeyRecorder:
    STOP_KEY = keyboard.Key.f9

    MODIFIERS = {
        keyboard.Key.ctrl: "ctrl",
        keyboard.Key.ctrl_r: "ctrl",
        keyboard.Key.alt: "alt",
        keyboard.Key.alt_r: "alt",
        keyboard.Key.shift: "shift",
        keyboard.Key.shift_r: "shift",
        keyboard.Key.cmd: "cmd",
        keyboard.Key.cmd_r: "cmd",
    }

    SHIFT_SYMBOLS = {
        "!": "1", "@": "2", "#": "3", "$": "4", "%": "5",
        "^": "6", "&": "7", "*": "8", "(": "9", ")": "0",
        "_": "-", "+": "=", ":": ";", '"': "'", "<": ",",
        ">": ".", "?": "/", "~": "`", "{": "[", "}": "]",
        "|": "\\",
    }

    def __init__(self, on_stop=None):
        self._on_stop = on_stop
        self._held = []
        self._tokens = []
        self.recording = False

    def start(self):
        self._held = []
        self._tokens = []
        self.recording = True

    def stop(self):
        self.recording = False

    def get_sequence(self):
        return ",".join(self._tokens)

    def _mod_name(self, key):
        return self.MODIFIERS.get(key)

    def _key_name(self, key):
        if isinstance(key, keyboard.Key):
            return key.name
        if isinstance(key, keyboard.KeyCode):
            char = key.char
            if char is None:
                return None
            if char.isalpha():
                return char.lower()
            if char in self.SHIFT_SYMBOLS:
                return self.SHIFT_SYMBOLS[char]
            return char
        return None

    def handle_press(self, key):
        if not self.recording:
            return
        if key == self.STOP_KEY:
            self.stop()
            if self._on_stop:
                self._on_stop()
            return
        mod = self._mod_name(key)
        if mod:
            if mod not in self._held:
                self._held.append(mod)
            return
        name = self._key_name(key)
        if name is None:
            return
        prefix = "+".join(self._held)
        self._tokens.append(f"{prefix}+{name}" if prefix else name)

    def handle_release(self, key):
        if not self.recording:
            return
        mod = self._mod_name(key)
        if mod and mod in self._held:
            self._held.remove(mod)