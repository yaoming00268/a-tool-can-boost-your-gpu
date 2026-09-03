import os
import ctypes
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
from plugins.base_plugin import BasePlugin
from core.gpu_service import GPUService
from core.icon_helper import IconHelper


class ProcessCapturePlugin(BasePlugin):
    plugin_id = "capture"
    plugin_name = "进程捕获与窗口扫描插件"
    order = 30

    def get_api_methods(self):
        return {
            "capture_foreground_app": self.capture_foreground_app,
            "get_running_windows_processes": self.get_running_windows_processes
        }

    def capture_foreground_app(self, delay_seconds=0):
        info = GPUService.capture_foreground_app_info(delay_seconds=int(delay_seconds))
        if info and info.get("exe_path") and os.path.exists(info["exe_path"]):
            icon_b64 = IconHelper.get_icon_base64(info["exe_path"])
            info["icon"] = icon_b64
            if self.context.get("log"):
                self.context["log"](f"成功捕获前台程序: [{info['name']}] ({info['exe_name']})")
            return {"success": True, "app": info}
        return {"success": False, "msg": "未检测到有效的前台运行程序"}

    def get_running_windows_processes(self):
        results = []
        seen_pids = set()
        seen_paths = set()
        current_pid = os.getpid()

        if os.name == "nt":
            user32 = ctypes.windll.user32

            def enum_proc(hwnd, lParam):
                if user32.IsWindowVisible(hwnd):
                    length = user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        pid = ctypes.c_ulong()
                        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                        if pid.value > 0 and pid.value != current_pid and pid.value not in seen_pids:
                            try:
                                proc = psutil.Process(pid.value)
                                exe_path = proc.exe()
                                if exe_path and os.path.exists(exe_path) and exe_path.lower() not in seen_paths:
                                    buff = ctypes.create_unicode_buffer(length + 1)
                                    user32.GetWindowTextW(hwnd, buff, length + 1)
                                    win_title = buff.value.strip()

                                    exe_name = proc.name()
                                    display_name = win_title if (win_title and len(win_title) < 35) else os.path.splitext(exe_name)[0]
                                    icon_b64 = IconHelper.get_icon_base64(exe_path)

                                    seen_pids.add(pid.value)
                                    seen_paths.add(exe_path.lower())
                                    results.append({
                                        "pid": pid.value,
                                        "name": display_name,
                                        "exe_name": exe_name,
                                        "exe_path": os.path.normpath(exe_path),
                                        "window_title": win_title,
                                        "icon": icon_b64
                                    })
                            except Exception:
                                pass
                return True

            EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
            user32.EnumWindows(EnumWindowsProc(enum_proc), 0)

        return sorted(results, key=lambda x: x["name"].lower())
