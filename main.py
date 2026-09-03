import os
import sys
import ctypes

# ── 打包运行引导：冻结(exe)模式下将 exe 所在目录设为工作目录并加入模块搜索路径 ──
if getattr(sys, "frozen", False):
    _app_dir = os.path.dirname(sys.executable)
    if _app_dir not in sys.path:
        sys.path.insert(0, _app_dir)
    os.chdir(_app_dir)

import webview
from core.data_manager import SoftwareDataManager
from core.gpu_service import elevate_privileges, is_admin
from core.hotkey_manager import HotkeyManager
from core.monitor_core import MonitorCore
from core.process_guard import install_process_guard
from plugins.plugin_manager import PluginManager
from api_bridge import SoftwareManagerAPI


def hide_console_window():
    if sys.platform == "win32":
        try:
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 0)
        except Exception:
            pass


def main():
    hide_console_window()
    install_process_guard()
    if sys.platform == "win32" and not is_admin():
        elevate_privileges()

    data_mgr = SoftwareDataManager()

    def status_cb(text, color):
        pass

    # 构建 monitor 实例
    monitor = MonitorCore(data_mgr, log_callback=None, status_callback=status_cb)

    plugin_context = {
        "data_mgr": data_mgr,
        "monitor_core": monitor,
        "log": None
    }
    plugin_mgr = PluginManager(plugin_context)
    plugin_mgr.discover_and_load()

    api = SoftwareManagerAPI(data_mgr, monitor, plugin_mgr)

    # 将调度核心日志通道完全绑定到 API 网关日志处理器
    monitor.log_callback = api.log
    plugin_context["log"] = api.log

    # 若偏好设置开启自动启动监控，则随应用启动自动开启后台调度
    if data_mgr.get_settings().get("auto_start_monitor", True):
        monitor.start()

    def on_hotkey():
        api.toggle_monitor()

    hotkey = data_mgr.get_settings().get("hotkey", "F12")
    hotkey_mgr = HotkeyManager(on_hotkey)
    hotkey_mgr.set_hotkey(hotkey)
    hotkey_mgr.start()

    html_path = os.path.abspath(os.path.join("web", "index.html"))

    window = webview.create_window(
        title="Nanako App Manager",
        url=f"file:///{html_path}",
        js_api=api,
        width=1100,
        height=800,
        min_size=(920, 620),
        background_color="#F4F6F9"
    )

    def on_closed():
        hotkey_mgr.stop()
        if monitor.monitoring:
            monitor.stop()
        plugin_mgr.notify_shutdown()

    window.events.closed += on_closed
    webview.start(debug=False)


if __name__ == "__main__":
    main()
