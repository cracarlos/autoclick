from autoclicker.gui import AutoClickApp
from autoclicker.hotkeys import HotkeyManager


def main():
    app = AutoClickApp()
    hotkeys = HotkeyManager(
        on_toggle_click=lambda: app._push_action("click"),
        on_toggle_keyboard=lambda: app._push_action("keyboard"),
        on_capture=lambda: app._push_action("capture"),
    )
    hotkeys.start()
    app.set_hotkeys(hotkeys)
    try:
        app.mainloop()
    finally:
        hotkeys.stop()


if __name__ == "__main__":
    main()