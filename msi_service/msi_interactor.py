import sys
import os
import time
import subprocess

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class MSIInteractor:
    @staticmethod
    def is_running() -> bool:
        if not HAS_PSUTIL:
            return False
        try:
            for proc in psutil.process_iter(['name']):
                pname = proc.info['name']
                if pname and 'msiafterburner' in pname.lower():
                    return True
            return False
        except Exception:
            return False

    @classmethod
    def launch_afterburner(cls, install_path: str | None) -> tuple[bool, str]:
        if not install_path:
            return False, "未找到微星小飞机安装路径"
        exe_path = os.path.join(install_path, "MSIAfterburner.exe")
        if not os.path.exists(exe_path):
            return False, "未找到MSIAfterburner.exe"

        try:
            if cls.is_running():
                return True, "微星小飞机已在运行"
            creation_flags = 0x08000000 if sys.platform == "win32" else 0
            subprocess.Popen(f'"{exe_path}"', shell=True, creationflags=creation_flags)
            return True, "已启动微星小飞机"
        except Exception as e:
            return False, f"启动微星小飞机失败: {str(e)}"

    @classmethod
    def open_curve_editor(cls, install_path: str | None) -> tuple[bool, str]:
        if not install_path and not cls.is_running():
            return False, "未找到微星小飞机安装路径"

        if not cls.is_running():
            success, msg = cls.launch_afterburner(install_path)
            if not success:
                return False, msg

        for _ in range(10):
            if cls.is_running():
                break
            time.sleep(0.5)

        if sys.platform == "win32":
            hwnd = cls._find_window()
            if hwnd:
                cls._activate_window_and_send_hotkey(hwnd, 0x46)
                return True, "已成功打开微星小飞机并调出 Curve Editor 曲线编辑器"

        return True, "微星小飞机已启动"

    @classmethod
    def apply_profile(cls, install_path: str | None, profile_id: int | str) -> tuple[bool, str]:
        if not profile_id or profile_id == "默认配置" or profile_id == 0:
            return True, "使用默认配置"

        if not install_path:
            return False, "未找到微星小飞机安装路径"

        exe_path = os.path.join(install_path, "MSIAfterburner.exe")
        if not os.path.exists(exe_path):
            return False, "未找到MSIAfterburner.exe"

        try:
            if not cls.is_running():
                success, msg = cls.launch_afterburner(install_path)
                if not success:
                    return False, msg
                time.sleep(1.5)

            creation_flags = 0x08000000 if sys.platform == "win32" else 0
            cmd = f'"{exe_path}" -Profile{profile_id}'
            subprocess.Popen(cmd, shell=True, creationflags=creation_flags)

            if sys.platform == "win32":
                hwnd = cls._find_window()
                if hwnd:
                    vk_num = 0x30 + int(profile_id)
                    cls._activate_window_and_send_hotkey(hwnd, vk_num)

            return True, f"已应用 Profile{profile_id}"
        except Exception as e:
            return False, f"应用配置失败: {str(e)}"

    @staticmethod
    def _find_window():
        import ctypes
        user32 = ctypes.windll.user32
        hwnd = user32.FindWindowW("MSIAfterburnerClass", None)
        if not hwnd:
            def enum_cb(h, extra):
                nonlocal hwnd
                if user32.IsWindowVisible(h):
                    length = user32.GetWindowTextLengthW(h)
                    buff = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(h, buff, length + 1)
                    if "MSI Afterburner" in buff.value:
                        hwnd = h
                        return False
                return True

            EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
            user32.EnumWindows(EnumWindowsProc(enum_cb), 0)
        return hwnd

    @staticmethod
    def _activate_window_and_send_hotkey(hwnd, key_code: int):
        import ctypes
        user32 = ctypes.windll.user32
        user32.ShowWindow(hwnd, 9)
        user32.SetForegroundWindow(hwnd)
        time.sleep(0.2)
        VK_CONTROL = 0x11
        KEYEVENTF_KEYUP = 0x0002
        user32.keybd_event(VK_CONTROL, 0, 0, 0)
        user32.keybd_event(key_code, 0, 0, 0)
        time.sleep(0.05)
        user32.keybd_event(key_code, 0, KEYEVENTF_KEYUP, 0)
        user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
