import subprocess
import sys
import time
from plugins.base_plugin import BasePlugin
from core.gpu_service import GPUService


class MonitorPlugin(BasePlugin):
    plugin_id = "monitor"
    plugin_name = "核心调频监控控制"
    slot = "main"
    order = 30

    def get_api_methods(self):
        return {
            "toggle_monitor": self.toggle_monitor,
            "get_status": self.get_status,
            "set_only_foreground": self.set_only_foreground,
            "detect_foreground": self.detect_foreground,
            "open_taskmgr": self.open_taskmgr
        }

    def toggle_monitor(self):
        core = self.context.get("monitor_core")
        if not core:
            return {"running": False, "msg": "核心未初始化"}

        if not core.monitoring:
            core.start()
            self.context["log"]("调频监控服务已启动")
        else:
            core.stop()
            self.context["log"]("监控服务已停止")

        return self.get_status()

    def get_status(self):
        core = self.context.get("monitor_core")
        cfg = self.context.get("config_mgr")
        running = core.monitoring if core else False
        only_fg = cfg.get_only_foreground() if cfg else True
        status_text = core.current_status_text if (core and hasattr(core, "current_status_text")) else ("服务就绪" if running else "未运行")
        return {
            "running": running,
            "only_foreground": only_fg,
            "status_text": status_text
        }

    def set_only_foreground(self, enabled):
        if "config_mgr" in self.context:
            self.context["config_mgr"].set_only_foreground(enabled)
        mode = "仅前台窗口生效" if enabled else "后台运行全量生效"
        self.context["log"](f"监控策略变更为: {mode}")
        return True

    def detect_foreground(self):
        proc = GPUService.get_active_foreground_process_name()
        return proc or ""

    def open_taskmgr(self):
        if sys.platform == "win32":
            import ctypes
            u = ctypes.windll.user32
            u.keybd_event(0x11, 0, 0, 0)
            u.keybd_event(0x10, 0, 0, 0)
            u.keybd_event(0x1B, 0, 0, 0)
            time.sleep(0.05)
            u.keybd_event(0x1B, 0, 2, 0)
            u.keybd_event(0x10, 0, 2, 0)
            u.keybd_event(0x11, 0, 2, 0)
        else:
            subprocess.Popen(["taskmgr"])
        return True
