# monitor_core.py
import threading
import time
import psutil
from gpu_service import GPUService
from msi_service import MSIAfterburnerService


class MonitorCore:
    def __init__(self, config_mgr, log_callback, status_callback):
        self.config_mgr = config_mgr
        self.log_callback = log_callback
        self.status_callback = status_callback
        self.monitoring = False
        self.current_locked_state = None
        self.current_msi_profile = None
        self._thread = None
        self.msi_service = MSIAfterburnerService()

    def start(self):
        if self.monitoring:
            return

        if self.msi_service.is_installed() and not self.msi_service.is_running():
            self.log_callback("正在启动微星小飞机...")
            success, msg = self.msi_service.launch_afterburner()
            self.log_callback(msg)
            if success:
                time.sleep(2)

        self.monitoring = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self.monitoring = False
        if self.current_locked_state is not None:
            success, msg = GPUService.reset_frequency()
            self.log_callback(msg)
            self.current_locked_state = None

    def _apply_msi_profile(self, profile_name):
        """应用微星小飞机配置"""
        if not profile_name or profile_name == "默认配置":
            return True, "使用默认MSI配置"

        profile = self.msi_service.get_profile_by_name(profile_name)
        if not profile:
            return False, f"未找到MSI配置: {profile_name}"

        if self.current_msi_profile == profile_name:
            return True, f"MSI配置 {profile_name} 已应用"

        success, msg = self.msi_service.apply_profile(profile['id'])
        if success:
            self.current_msi_profile = profile_name
        return success, msg

    def _monitor_loop(self):
        while self.monitoring:
            active_profile = self.config_mgr.get_active_profile_name()
            rules = self.config_mgr.get_profile_rules(active_profile)

            if not rules:
                if self.current_locked_state is not None:
                    GPUService.reset_frequency()
                    self.current_locked_state = None
                    self.log_callback("当前配置规则为空，恢复默认频率")
                time.sleep(1.5)
                continue

            matched_rules = []
            only_fg = self.config_mgr.get_only_foreground()

            if only_fg:
                fg_proc = GPUService.get_active_foreground_process_name()
                if fg_proc:
                    fg_proc_lower = fg_proc.lower()
                    for rule in rules:
                        if rule['process'].lower() == fg_proc_lower:
                            matched_rules.append(rule)
                            break
            else:
                running_proc_names = set()
                for p in psutil.process_iter(['name']):
                    try:
                        name = p.info['name']
                        if name:
                            running_proc_names.add(name.lower())
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

                for rule in rules:
                    if rule['process'].lower() in running_proc_names:
                        matched_rules.append(rule)
                        break

            if matched_rules:
                target_rule = matched_rules[0]
                mode = target_rule.get("mode", "定频模式")
                msi_profile = target_rule.get("msi_profile", None)

                if mode == "定频模式":
                    f = target_rule.get("frequency", 2200)
                    target_state = (f, f)
                    desc = f"{f}MHz"
                else:
                    min_f = target_rule.get("min_freq", 200)
                    max_f = target_rule.get("max_freq", 4000)
                    target_state = (min_f, max_f)
                    desc = f"{min_f}-{max_f}MHz"

                if self.current_locked_state != target_state:
                    success, msg = GPUService.set_frequency(target_state[0], target_state[1])
                    self.log_callback(f"检测到前台/目标窗口运行 [{target_rule['process']}] -> {msg}")
                    if success:
                        self.current_locked_state = target_state

                if msi_profile and msi_profile != "默认配置":
                    msi_success, msi_msg = self._apply_msi_profile(msi_profile)
                    if msi_success and self.current_msi_profile != msi_profile:
                        self.log_callback(f"已应用微星小飞机配置: {msi_profile}")

                status_str = f"状态: 运行中 (锁定 {desc})"
                if msi_profile and msi_profile != "默认配置":
                    status_str += f" [MSI: {msi_profile}]"
                self.status_callback(status_str, "green")
            else:
                if self.current_locked_state is not None:
                    success, msg = GPUService.reset_frequency()
                    self.log_callback(f"目标前台/后台窗口已退出或失去焦点 -> {msg}")
                    self.current_locked_state = None
                    mode_desc = "前台模式" if only_fg else "后台排队模式"
                    status_str = f"状态: 监控中 [{mode_desc} | 配置: {active_profile}]"
                    self.status_callback(status_str, "blue")

            time.sleep(1.5)
