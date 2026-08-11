import ctypes
import threading
import time


class HotkeyManager:
    """后台全局快捷键轮询服务 (不依赖第三方库，直接调用 Windows API)"""

    def __init__(self, callback):
        self.callback = callback
        self.running = False
        self.vk_code = 0x7B  # 默认 F12
        self.mod_ctrl = False
        self.mod_alt = False
        self.mod_shift = False

        self.vk_map = {
            "F1": 0x70, "F2": 0x71, "F3": 0x72, "F4": 0x73,
            "F5": 0x74, "F6": 0x75, "F7": 0x76, "F8": 0x77,
            "F9": 0x78, "F10": 0x79, "F11": 0x7A, "F12": 0x7B,
            "HOME": 0x24, "END": 0x23, "PAGEUP": 0x21, "PAGEDOWN": 0x22
        }

    def set_hotkey(self, hotkey_str):
        if not hotkey_str or hotkey_str == "无":
            self.vk_code = None
            return

        parts = hotkey_str.upper().split("+")
        self.mod_ctrl = "CTRL" in parts
        self.mod_alt = "ALT" in parts
        self.mod_shift = "SHIFT" in parts

        key = parts[-1].strip()
        self.vk_code = self.vk_map.get(key, 0x7B)

    def start(self):
        if self.running: return
        self.running = True
        threading.Thread(target=self._poll_loop, daemon=True).start()

    def stop(self):
        self.running = False

    def _poll_loop(self):
        user32 = ctypes.windll.user32
        was_pressed = False

        while self.running:
            time.sleep(0.05)
            if not self.vk_code:
                continue

            # GetAsyncKeyState 获取按键状态
            key_down = (user32.GetAsyncKeyState(self.vk_code) & 0x8000) != 0
            ctrl_down = (user32.GetAsyncKeyState(0x11) & 0x8000) != 0
            alt_down = (user32.GetAsyncKeyState(0x12) & 0x8000) != 0
            shift_down = (user32.GetAsyncKeyState(0x10) & 0x8000) != 0

            modifiers_match = (
                    (self.mod_ctrl == ctrl_down) and
                    (self.mod_alt == alt_down) and
                    (self.mod_shift == shift_down)
            )

            is_pressed = key_down and modifiers_match

            if is_pressed and not was_pressed:
                # 在主线程中触发 UI 回调
                self.callback()
                was_pressed = True
            elif not is_pressed:
                was_pressed = False