# ui_app/app_main.py
import threading
import tkinter as tk
import psutil

from config_manager import ConfigManager
from ui_components import AdminFrame, ProfileFrame, RuleFrame, ControlFrame, LogFrame
from hotkey_manager import HotkeyManager

from import_dialog import ImportAppsDialog
from process_dialog import ProcessSearchDialog
from settings_dialog import SettingsDialog

# 导入抽离的控制器
from ui_app.profile_rule_controller import ProfileRuleController
from ui_app.msi_controller import MSIController
from ui_app.monitor_controller import MonitorController


class GPUFrequencyBoosterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NVIDIA 显卡多程序多配置频率锁定工具")
        self.root.geometry("900x850")
        self.root.resizable(False, False)

        self.config_mgr = ConfigManager()
        self.msi_service = None
        self.monitor_core = None
        self.rule_icons = []

        # 实例化子控制器 (依赖注入)
        self.profile_rule_ctrl = ProfileRuleController(self)
        self.msi_ctrl = MSIController(self)
        self.monitor_ctrl = MonitorController(self)

        # 初始化快捷键管理器
        self.hotkey_mgr = HotkeyManager(self.monitor_ctrl.trigger_hotkey_toggle)

        self.build_ui()
        self.log("🚀 界面已启动，正在后台加载配置...")

        threading.Thread(target=self._background_startup, daemon=True).start()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def build_ui(self):
        top_bar = tk.Frame(self.root)
        top_bar.pack(fill="x", padx=15, pady=2)
        tk.Button(top_bar, text="⚙️ 软件全局设置", command=self.open_settings_dialog, bg="#ECEFF1",
                  font=("微软雅黑", 9)).pack(side="right")

        self.admin_frame = AdminFrame(self.root, self)
        self.admin_frame.pack(pady=5)
        self.profile_frame = ProfileFrame(self.root, self)
        self.profile_frame.pack(fill="x", padx=15, pady=4)
        self.rule_frame = RuleFrame(self.root, self)
        self.rule_frame.pack(fill="x", padx=15, pady=4)
        self.control_frame = ControlFrame(self.root, self, self.config_mgr)
        self.control_frame.pack(fill="x", padx=15, pady=4)
        self.log_frame = LogFrame(self.root)
        self.log_frame.pack(fill="both", expand=True, padx=15, pady=4)

    # --- Properties 透传 ---
    @property
    def combo_profiles(self): return self.profile_frame.combo_profiles
    @property
    def var_rule_search(self): return self.rule_frame.var_rule_search
    @property
    def tree_rules(self): return self.rule_frame.tree_rules
    @property
    def combo_process_input(self): return self.rule_frame.combo_process_input
    @property
    def combo_mode(self): return self.rule_frame.combo_mode
    @property
    def entry_freq_input(self): return self.rule_frame.entry_freq_input
    @property
    def entry_min_freq(self): return self.rule_frame.entry_min_freq
    @property
    def entry_max_freq(self): return self.rule_frame.entry_max_freq
    @property
    def combo_msi_profile(self): return self.rule_frame.combo_msi_profile
    @property
    def lbl_msi_info(self): return self.rule_frame.lbl_msi_info
    @property
    def btn_toggle(self): return self.control_frame.btn_toggle
    @property
    def lbl_status(self): return self.control_frame.lbl_status
    @property
    def var_only_foreground(self): return self.control_frame.var_only_foreground

    # --- UI 辅助方法 ---
    def log(self, message):
        self.root.after(0, lambda: self.log_frame.append_log(message))

    def update_status(self, text, color):
        self.root.after(0, lambda: self.lbl_status.config(text=text, fg=color))

    # --- 对外 Delegate 映射 ---
    def create_new_profile(self): self.profile_rule_ctrl.create_new_profile()
    def rename_current_profile(self): self.profile_rule_ctrl.rename_current_profile()
    def delete_current_profile(self): self.profile_rule_ctrl.delete_current_profile()
    def on_profile_selected(self, event=None): self.profile_rule_ctrl.on_profile_selected(event)
    def on_rule_tree_selected(self, event=None): self.profile_rule_ctrl.on_rule_tree_selected(event)
    def clear_input_fields(self): self.profile_rule_ctrl.clear_input_fields()
    def add_or_update_rule(self): self.profile_rule_ctrl.add_or_update_rule()
    def delete_selected_rule(self): self.profile_rule_ctrl.delete_selected_rule()
    def launch_selected_rule(self): self.profile_rule_ctrl.launch_selected_rule()
    def apply_selected_msi_profile(self): self.msi_ctrl.apply_selected_msi_profile()
    def open_msi_vf_editor(self): self.msi_ctrl.open_msi_vf_editor()
    def on_only_foreground_changed(self): self.monitor_ctrl.on_only_foreground_changed()
    def detect_foreground_window(self): self.monitor_ctrl.detect_foreground_window()
    def toggle_monitoring(self): self.monitor_ctrl.toggle_monitoring()
    def open_task_manager(self): self.monitor_ctrl.open_task_manager()

    # --- 弹窗入口 ---
    def open_settings_dialog(self):
        SettingsDialog(self.root, self.config_mgr, self.monitor_ctrl.apply_settings)

    def open_import_dialog(self):
        active_profile = self.combo_profiles.get().strip()
        if not active_profile:
            tk.messagebox.showwarning("提示", "请先创建或选择一个配置")
            return
        ImportAppsDialog(self.root, active_profile,
                         lambda exe, freq: self.profile_rule_ctrl.add_rule_direct(exe, "定频模式", freq, 200, 4000,
                                                                                  "默认配置"))

    def open_process_search_dialog(self):
        ProcessSearchDialog(self.root, lambda proc: self.combo_process_input.set(proc))

    # --- 生命周期管理 ---
    def _background_startup(self):
        from monitor_core import MonitorCore
        self.monitor_core = MonitorCore(self.config_mgr, self.log, self.update_status)
        self.msi_service = self.monitor_core.msi_service

        processes = set()
        for proc in psutil.process_iter(['name']):
            try:
                name = proc.info['name']
                if name and name.lower().endswith('.exe'):
                    processes.add(name)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        sorted_procs = sorted(list(processes), key=lambda s: s.lower())

        self.root.after(0, lambda: self._on_startup_complete(sorted_procs))

    def _on_startup_complete(self, sorted_procs):
        self.combo_process_input['values'] = sorted_procs
        if sorted_procs and not self.combo_process_input.get():
            self.combo_process_input.current(0)

        self.profile_rule_ctrl.load_profile_list()
        self.msi_ctrl.load_msi_profiles()
        self.msi_ctrl.check_msi_afterburner()

        self.monitor_ctrl.apply_settings()
        self.log("✅ 所有系统组件加载完毕！")

        settings = self.config_mgr.get_settings()
        auto_profile = settings.get("auto_profile", "不自动启用")
        if auto_profile != "不自动启用" and auto_profile in self.combo_profiles['values']:
            self.combo_profiles.set(auto_profile)
            self.profile_rule_ctrl.on_profile_selected()
            self.monitor_ctrl.toggle_monitoring()
            self.log(f"⚡ 已根据设置，自动启用配置: [{auto_profile}]")

    def on_closing(self):
        self.hotkey_mgr.stop()
        if self.monitor_core and self.monitor_core.monitoring:
            self.monitor_core.stop()
        self.root.destroy()