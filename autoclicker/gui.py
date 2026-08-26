import queue
import tkinter as tk
from tkinter import ttk, messagebox

from pynput.mouse import Controller as MouseController

from .engine import ClickConfig, ClickWorker, KeyboardConfig, KeyboardWorker
from .hotkeys import KeyRecorder


class AutoClickApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AutoClick")
        self.geometry("460x380")
        self.resizable(False, False)

        self._mouse = MouseController()
        self._status_queue = queue.Queue()
        self._action_queue = queue.Queue()

        self.click_cfg = ClickConfig(on_status=lambda m: self._status_queue.put(("click", m)))
        self.kb_cfg = KeyboardConfig(on_status=lambda m: self._status_queue.put(("keyboard", m)))
        self.click_worker = ClickWorker(self.click_cfg)
        self.kb_worker = KeyboardWorker(self.kb_cfg)
        self.recorder = None
        self._hotkeys = None

        self.captured_x = tk.StringVar(value="0")
        self.captured_y = tk.StringVar(value="0")
        self.click_status = tk.StringVar(value="click STOPPED")
        self.kb_status = tk.StringVar(value="keyboard STOPPED")

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.after(100, self._poll_status)

    def _push_action(self, name):
        self._action_queue.put(name)

    def set_hotkeys(self, hotkeys):
        self._hotkeys = hotkeys

    def _build_ui(self):
        self._build_menu()

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=8, pady=8)

        click_tab = ttk.Frame(nb)
        kb_tab = ttk.Frame(nb)
        nb.add(click_tab, text="Autoclick")
        nb.add(kb_tab, text="Teclado")

        self._build_click_tab(click_tab)
        self._build_kb_tab(kb_tab)
        self._build_status_bar()
        self._build_legend()

    def _build_menu(self):
        menubar = tk.Menu(self)
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Atajos de teclado", command=self._show_help)
        menubar.add_cascade(label="Ayuda", menu=help_menu)
        self.config(menu=menubar)

    def _show_help(self):
        messagebox.showinfo(
            "Atajos de teclado",
            "Teclas globales (funcionan en toda la PC):\n\n"
            "F6  Iniciar / detener el autoclick\n"
            "F7  Iniciar / detener la macro de teclado\n"
            "F8  Capturar la posición actual del cursor\n"
            "F9  Detener la grabación de teclas\n\n"
            "Consejos:\n"
            "- Repeticiones en 0 = infinitas.\n"
            "- Posición 'Cursor actual' hace click donde esté el mouse.\n"
            "- Teclas de macro: ctrl+c, enter, a, shift+tab... separadas por coma.",
        )

    def _build_click_tab(self, parent):
        pad = {"padx": 8, "pady": 4, "sticky": "w"}

        ttk.Label(parent, text="Intervalo (ms):").grid(row=0, column=0, **pad)
        self.interval = ttk.Spinbox(parent, from_=1, to=10000, increment=10, width=10)
        self.interval.set(self.click_cfg.interval_ms)
        self.interval.grid(row=0, column=1, **pad)

        ttk.Label(parent, text="Repeticiones (0 = infinitas):").grid(row=1, column=0, **pad)
        self.repeat = ttk.Spinbox(parent, from_=0, to=100000, increment=1, width=10)
        self.repeat.set(self.click_cfg.repeat)
        self.repeat.grid(row=1, column=1, **pad)

        ttk.Label(parent, text="Posición:").grid(row=2, column=0, **pad)
        pos_frame = ttk.Frame(parent)
        pos_frame.grid(row=2, column=1, columnspan=2, sticky="w")
        self.pos_mode = tk.StringVar(value="current")
        ttk.Radiobutton(pos_frame, text="Cursor actual", variable=self.pos_mode, value="current").pack(side="left")
        ttk.Radiobutton(pos_frame, text="Fija", variable=self.pos_mode, value="fixed").pack(side="left", padx=(8, 0))

        coord_frame = ttk.Frame(parent)
        coord_frame.grid(row=3, column=1, columnspan=2, sticky="w")
        ttk.Label(coord_frame, text="X:").pack(side="left")
        self.fixed_x = ttk.Entry(coord_frame, width=6, textvariable=self.captured_x)
        self.fixed_x.pack(side="left", padx=(0, 8))
        ttk.Label(coord_frame, text="Y:").pack(side="left")
        self.fixed_y = ttk.Entry(coord_frame, width=6, textvariable=self.captured_y)
        self.fixed_y.pack(side="left")
        ttk.Button(coord_frame, text="Capturar (F8)", command=self._capture_position).pack(side="left", padx=(12, 0))

        ttk.Label(parent, text="Tipo de click:").grid(row=4, column=0, **pad)
        btn_frame = ttk.Frame(parent)
        btn_frame.grid(row=4, column=1, columnspan=2, sticky="w")
        self.btn_var = tk.StringVar(value="left")
        for label, value in (("Izquierdo", "left"), ("Derecho", "right"), ("Medio", "middle")):
            ttk.Radiobutton(btn_frame, text=label, variable=self.btn_var, value=value).pack(side="left", padx=(0, 8))
        self.double_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(btn_frame, text="Doble", variable=self.double_var).pack(side="left")

        self.click_btn = ttk.Button(parent, text="Iniciar click  [F6]", command=self._toggle_click)
        self.click_btn.grid(row=5, column=0, columnspan=2, padx=8, pady=12)

    def _build_kb_tab(self, parent):
        pad = {"padx": 8, "pady": 4, "sticky": "w"}

        ttk.Label(parent, text="Teclas (separadas por coma, ej: ctrl+c,enter,a):").grid(row=0, column=0, **pad)
        self.sequence = ttk.Entry(parent, width=40)
        self.sequence.grid(row=1, column=0, columnspan=2, **pad)

        ttk.Label(parent, text="Intervalo (ms):").grid(row=2, column=0, **pad)
        self.kb_interval = ttk.Spinbox(parent, from_=1, to=10000, increment=10, width=10)
        self.kb_interval.set(self.kb_cfg.interval_ms)
        self.kb_interval.grid(row=2, column=1, **pad)

        ttk.Label(parent, text="Repeticiones (0 = infinitas):").grid(row=3, column=0, **pad)
        self.kb_repeat = ttk.Spinbox(parent, from_=0, to=100000, increment=1, width=10)
        self.kb_repeat.set(self.kb_cfg.repeat)
        self.kb_repeat.grid(row=3, column=1, **pad)

        self.record_btn = ttk.Button(parent, text="Grabar teclas  [F9]", command=self._toggle_record)
        self.record_btn.grid(row=4, column=0, columnspan=2, padx=8, pady=(0, 4))

        self.kb_btn = ttk.Button(parent, text="Iniciar teclado  [F7]", command=self._toggle_keyboard)
        self.kb_btn.grid(row=5, column=0, columnspan=2, padx=8, pady=12)

    def _build_status_bar(self):
        bar = ttk.Frame(self)
        bar.pack(fill="x", side="bottom", padx=8, pady=(0, 2))
        ttk.Label(bar, textvariable=self.click_status).pack(side="left", padx=(0, 12))
        ttk.Label(bar, textvariable=self.kb_status).pack(side="left")

    def _build_legend(self):
        legend = ttk.Frame(self)
        legend.pack(fill="x", side="bottom", padx=8, pady=(0, 6))
        ttk.Label(
            legend,
            text="F6 click · F7 teclado · F8 capturar posición · F9 detener grabación",
        ).pack(side="left")

    def _capture_position(self):
        x, y = self._mouse.position
        self.captured_x.set(str(x))
        self.captured_y.set(str(y))
        self.pos_mode.set("fixed")

    def _apply_click_config(self):
        self.click_cfg.interval_ms = max(1, round(float(self.interval.get())))
        self.click_cfg.repeat = max(0, round(float(self.repeat.get())))
        self.click_cfg.mode = self.pos_mode.get()
        self.click_cfg.button = self.btn_var.get()
        self.click_cfg.double = self.double_var.get()
        if self.click_cfg.mode == "fixed":
            self.click_cfg.x = round(float(self.captured_x.get()))
            self.click_cfg.y = round(float(self.captured_y.get()))

    def _apply_kb_config(self):
        self.kb_cfg.sequence = self.sequence.get()
        self.kb_cfg.interval_ms = max(1, round(float(self.kb_interval.get())))
        self.kb_cfg.repeat = max(0, round(float(self.kb_repeat.get())))

    def _toggle_click(self):
        if self.click_worker.is_running():
            self.click_worker.stop()
        else:
            try:
                self._apply_click_config()
            except ValueError as exc:
                messagebox.showerror("AutoClick", f"Configuración inválida: {exc}")
                return
            self.click_worker.start()

    def _toggle_keyboard(self):
        if self.kb_worker.is_running():
            self.kb_worker.stop()
        else:
            try:
                self._apply_kb_config()
            except ValueError as exc:
                messagebox.showerror("AutoClick", f"Configuración inválida: {exc}")
                return
            self.kb_worker.start()

    def _toggle_record(self):
        if self.recorder and self.recorder.recording:
            self._finish_record()
        else:
            self.recorder = KeyRecorder(on_stop=lambda: self._push_action("record"))
            if self._hotkeys:
                self._hotkeys.set_recorder(self.recorder)
            self.recorder.start()
            self.record_btn.config(text="Grabando... (F9 o clic para terminar)")

    def _finish_record(self):
        if self.recorder and self.recorder.recording:
            self.recorder.stop()
        if self.recorder:
            seq = self.recorder.get_sequence()
            self.sequence.delete(0, tk.END)
            self.sequence.insert(0, seq)
            self.recorder = None
        if self._hotkeys:
            self._hotkeys.set_recorder(None)
        self.record_btn.config(text="Grabar teclas  [F9]")

    def _poll_status(self):
        try:
            while True:
                kind, msg = self._status_queue.get_nowait()
                if kind == "click":
                    self.click_status.set(msg)
                    self.click_btn.config(text="Iniciar click  [F6]" if "STOP" in msg else "Detener click  [F6]")
                else:
                    self.kb_status.set(msg)
                    self.kb_btn.config(text="Iniciar teclado  [F7]" if "STOP" in msg else "Detener teclado  [F7]")
        except queue.Empty:
            pass
        try:
            while True:
                name = self._action_queue.get_nowait()
                if name == "click":
                    self._toggle_click()
                elif name == "keyboard":
                    self._toggle_keyboard()
                elif name == "capture":
                    self._capture_position()
                elif name == "record":
                    self._finish_record()
        except queue.Empty:
            pass
        self.after(100, self._poll_status)

    def _on_close(self):
        if self.recorder and self.recorder.recording:
            self.recorder.stop()
        if self._hotkeys:
            self._hotkeys.set_recorder(None)
        self.click_worker.stop()
        self.kb_worker.stop()
        self.destroy()