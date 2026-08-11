import sys
import time
import subprocess
from tkinter import messagebox
from gpu_service import GPUService, elevate_privileges, is_admin

class MonitorController:
    def __init__(self, app):
        self.app = app

    def apply_settings(self):
        settings = self.app.config_mgr.get_settings()
        hotkey = settings.get("hotkey", "F12")
        self.app.hotkey_mgr.set_hotkey(hotkey)
        self.app.hotkey_mgr.start()
        if hotkey != "无":
            self.app.log(f"已启用后台快捷键启停: [{hotkey}]")

    def trigger_hotkey_toggle(self):
        self.app.root.after(0, self.toggle_monitoring)

    def on_only_foreground_changed(self):
        enabled = self.app.var_only_foreground.get()
        self.app.config_mgr.set_only_foreground(enabled)
        mode_text = "仅前台活动窗口生效" if enabled else "系统后台运行全量匹配"
        self.app.log(f"已更新监控检测模式为: [{mode_text}]")

    def detect_foreground_window(self):
        proc_name = GPUService.get_ui_target_process_name()
        if proc_name:
            self.app.combo_process_input.set(proc_name)
            self.app.log(f"已自动识别并载入前台窗口进程: {proc_name}")
        else:
            messagebox.showinfo("提示", "未检测到有焦点的前台窗口")

    def toggle_monitoring(self):
        if not self.app.monitor_core:
            messagebox.showwarning("稍等", "核心服务正在初始化...")
            return

        if not self.app.monitor_core.monitoring:
            if not is_admin():
                if messagebox.askyesno("权限不足", "当前未获得管理员权限，是否自动获取？"):
                    success, msg = elevate_privileges()
                    if not success: messagebox.showwarning("提示", msg)
                return

            active_profile = self.app.combo_profiles.get().strip()
            if not self.app.config_mgr.get_profile_rules(active_profile):
                messagebox.showwarning("提示", "当前配置无规则")
                return

            self.app.btn_toggle.config(text="停止监控 (已由快捷键或点击启动)", bg="#F44336")
            mode = "前台模式" if self.app.var_only_foreground.get() else "后台全量"
            self.app.update_status(f"状态: 监控中 [{mode} | 配置: {active_profile}]", "blue")
            self.app.log(f"⚡ 启动监控 ({mode})，配置 [{active_profile}]")
            self.app.monitor_core.start()
        else:
            self.app.monitor_core.stop()
            self.app.btn_toggle.config(text="启动自动提频监控", bg="#4CAF50")
            self.app.update_status("状态: 监控已停止", "gray")
            self.app.log("🛑 已停止监控服务")

    def open_task_manager(self):
        if sys.platform == "win32":
            import ctypes
            user32 = ctypes.windll.user32
            VK_CONTROL, VK_SHIFT, VK_ESCAPE, KEYEVENTF_KEYUP = 0x11, 0x10, 0x1B, 0x0002

            user32.keybd_event(VK_CONTROL, 0, 0, 0)
            user32.keybd_event(VK_SHIFT, 0, 0, 0)
            user32.keybd_event(VK_ESCAPE, 0, 0, 0)
            time.sleep(0.05)
            user32.keybd_event(VK_ESCAPE, 0, KEYEVENTF_KEYUP, 0)
            user32.keybd_event(VK_SHIFT, 0, KEYEVENTF_KEYUP, 0)
            user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
            self.app.log("已发送快捷键 Ctrl+Shift+Esc 打开任务管理器")
        else:
            subprocess.Popen(["taskmgr"])
            self.app.log("已启动任务管理器")