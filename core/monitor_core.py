import os
import ctypes
import threading
import time
import sys

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from core.gpu_service import GPUService, is_admin
from core.power_service import PowerPlanService
from core.app_launcher import AppLauncher
from msi_service import MSIAfterburnerService


class MonitorCore:
    def __init__(self, data_mgr, log_callback, status_callback):
        self.data_mgr = data_mgr
        self._raw_log_callback = log_callback
        self.status_callback = status_callback or (lambda text, color: None)
        self.monitoring = False

        self.current_locked_gpu_state = None
        self.current_applied_power_plan = None
        self.current_msi_profile = None
        self.default_power_plan = None

        self.active_app_name = None
        self.last_foreground_proc = None
        self._last_matched_app_id = None
        self._unmatched_streak = 0
        self._tracked_running_pids = set()  # 全局模式下追踪运行中进程 PID，用于任何情况下的打开次数统计
        self.current_status_text = "未启动监控"
        self.current_status_color = "#888888"

        self.msi_service = MSIAfterburnerService()

        self._thread = None
        self._wake_event = threading.Event()

    @property
    def log_callback(self):
        return self._raw_log_callback

    @log_callback.setter
    def log_callback(self, cb):
        self._raw_log_callback = cb

    def log(self, msg):
        settings = self.data_mgr.get_settings()
        if settings.get("enable_logging", True) and self._raw_log_callback:
            self._raw_log_callback(msg)

    def update_status(self, text, color):
        self.current_status_text = text
        self.current_status_color = color
        if self.status_callback:
            try:
                self.status_callback(text, color)
            except Exception:
                pass

    def get_monitor_status(self):
        gpu_info = GPUService.detect_gpu_info()
        admin_ok = is_admin() if sys.platform == "win32" else True
        return {
            "monitoring": self.monitoring,
            "is_admin": admin_ok,
            "gpu_available": gpu_info.get("available", False),
            "gpu_name": gpu_info.get("name", "未知显卡"),
            "current_freq": gpu_info.get("current_freq"),
            "max_freq": gpu_info.get("max_freq"),
            "active_app": self.active_app_name or "无",
            "status_text": self.current_status_text,
            "status_color": self.current_status_color
        }

    def reapply_current_strategy(self):
        """规则修改后的热重载：清空当前锁定缓存，立即唤醒调度循环应用最新规则"""
        self.current_locked_gpu_state = None
        self.current_applied_power_plan = None
        self.current_msi_profile = None
        self.active_app_name = None
        self.log("[策略热重载] 检测到规则已修改，立即刷新并重新应用硬件策略...")
        self._wake_event.set()

    def start(self):
        if self.monitoring:
            return

        self.default_power_plan = PowerPlanService.get_active_plan_guid()

        # 权限与硬件初始状态检查
        if sys.platform == "win32" and not is_admin():
            self.log("[权限警告] 当前启动器未获得管理员权限！nvidia-smi 硬件锁频将无法生效，请点击顶部【获取管理员权限】重启提升权限！")

        gpu_info = GPUService.detect_gpu_info()
        if not gpu_info.get("available"):
            self.log("[硬件检测: 警告] 未检测到可调控的 NVIDIA 显卡或驱动未就绪，调频保护将被安全旁路，防止显卡失控狂飙")
        else:
            self.log(f"[硬件检测: 就绪] 成功识别显卡: {gpu_info.get('name')} (上限: {gpu_info.get('max_freq')} MHz, 当前: {gpu_info.get('current_freq') or '动态'} MHz)")

        auto_msi = self.data_mgr.get_settings().get("auto_launch_msi", True)
        if auto_msi and self.msi_service.is_installed() and not self.msi_service.is_running():
            self.log("[系统联动] 正在拉起微星小飞机 (MSI Afterburner)...")
            self.msi_service.launch_afterburner()

        self.monitoring = True
        self._unmatched_streak = 0
        self.log("[调度引擎] 自动调频与电源监控核心已启动")
        self.update_status("监控运行中 (等待目标应用)", "#10B981")
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self.monitoring = False
        self._wake_event.set()
        self._restore_defaults()
        self.update_status("监控已停止", "#888888")
        self.log("[调度引擎] 调频与电源监控已停止")

    def _restore_defaults(self):
        settings = self.data_mgr.get_settings()
        use_buffer = settings.get("enable_gpu_buffer", True)
        ramp_step = int(settings.get("gpu_ramp_step", 150))
        ramp_delay = float(settings.get("gpu_ramp_delay", 0.035))

        if self.current_locked_gpu_state is not None:
            if GPUService.is_gpu_available():
                if use_buffer:
                    GPUService.smooth_reset_frequency(step_mhz=ramp_step, delay_step=ramp_delay, log_cb=self.log)
                else:
                    GPUService.reset_frequency()
            self.current_locked_gpu_state = None

        if self.default_power_plan and self.current_applied_power_plan != self.default_power_plan:
            PowerPlanService.set_active_plan(self.default_power_plan)
            self.current_applied_power_plan = self.default_power_plan

        self.active_app_name = None
        self.last_foreground_proc = None
        self._last_matched_app_id = None
        self._unmatched_streak = 0
        self.update_status("空闲 (默认系统策略)", "#888888")

    def _get_running_process_names(self):
        names = set()
        if not HAS_PSUTIL:
            return names
        try:
            for p in psutil.process_iter(['name']):
                try:
                    name = p.info['name']
                    if name:
                        names.add(name.strip().lower())
                except Exception:
                    pass
        except Exception:
            pass
        return names

    def _monitor_loop(self):
        while self.monitoring:
            settings = self.data_mgr.get_settings()
            schedule_mode = settings.get("schedule_mode", "focus")
            global_mode = settings.get("global_mode", True)
            use_buffer = settings.get("enable_gpu_buffer", True)
            ramp_step = int(settings.get("gpu_ramp_step", 150))
            ramp_delay = float(settings.get("gpu_ramp_delay", 0.035))

            matched_app = None
            window_state_desc = "未运行"

                        # 存活检测：清理已退出的应用 PID，确保下次打开可再次准确统计
            if self._tracked_running_pids:
                dead_pids = set()
                for pid in self._tracked_running_pids:
                    try:
                        if sys.platform == "win32":
                            kernel32 = ctypes.windll.kernel32
                            h_proc = kernel32.OpenProcess(0x1000, False, pid)
                            if h_proc:
                                exit_code = ctypes.c_ulong()
                                kernel32.GetExitCodeProcess(h_proc, ctypes.byref(exit_code))
                                kernel32.CloseHandle(h_proc)
                                if exit_code.value != 259:  # STILL_ACTIVE = 259
                                    dead_pids.add(pid)
                            else:
                                dead_pids.add(pid)
                        elif HAS_PSUTIL:
                            if not psutil.pid_exists(pid):
                                dead_pids.add(pid)
                    except Exception:
                        dead_pids.add(pid)
                self._tracked_running_pids -= dead_pids

            active_proc, active_pid, full_path = GPUService.get_active_foreground_process_info()

            # 1. 焦点窗口模式
            if schedule_mode == "focus":
                # 当用户处于本管理器窗口时，保持上一活动应用的最新策略（实时从数据管理器重载）
                if active_proc == "__SELF__":
                    if self._last_matched_app_id:
                        reloaded_app = self.data_mgr.get_app_by_id(self._last_matched_app_id)
                        if reloaded_app:
                            matched_app = reloaded_app
                            window_state_desc = "前台保持 (查看主程序)"
                elif active_proc:
                    if global_mode or AppLauncher.is_process_launched_by_manager(active_proc, pid=active_pid):
                        # 传入 full_path 与 active_pid 实现防串名精准解析
                        found_app = self.data_mgr.get_app_by_process(active_proc, full_path=full_path, pid=active_pid)
                        if found_app:
                            matched_app = found_app
                            window_state_desc = "前台焦点窗口 (Focus)"

                # 焦点防抖缓冲：如瞬时未识别（切屏、全屏切换、窗口重绘），给予短暂缓冲周期（2次采样）
                if not matched_app and self._last_matched_app_id:
                    self._unmatched_streak += 1
                    if self._unmatched_streak <= 2:
                        reloaded_app = self.data_mgr.get_app_by_id(self._last_matched_app_id)
                        if reloaded_app:
                            matched_app = reloaded_app
                            window_state_desc = f"焦点保持中 (失焦防抖缓冲 {self._unmatched_streak}/2)"
                else:
                    if matched_app and active_proc != "__SELF__":
                        self._unmatched_streak = 0

            # 2. 排队器模式
            elif schedule_mode == "queue":
                running_names = self._get_running_process_names()
                ordered_apps = self.data_mgr.get_queue_order_apps()
                for rank, app in enumerate(ordered_apps, start=1):
                    exe = (app.get("exe_name") or "").strip().lower()
                    if exe and exe in running_names:
                        if not global_mode and not AppLauncher.is_process_launched_by_manager(exe):
                            continue
                        matched_app = app
                        is_fg = (active_proc and active_proc != "__SELF__" and active_proc.strip().lower() == exe)
                        window_state_desc = f"排队器首位 (Rank #{rank}, {'前台' if is_fg else '后台运行'})"
                        break

            # 窗口状态转移与显式日志
            if active_proc != self.last_foreground_proc and active_proc != "__SELF__":
                if matched_app:
                    self.log(f"[窗口状态: 焦点激活] 进程 [{active_proc}] -> 命中应用: [{matched_app['name']}] ({window_state_desc})")
                else:
                    if self.active_app_name and self._unmatched_streak > 2:
                        self.log(f"[窗口状态: 窗口失焦] 原应用 [{self.active_app_name}] 失去焦点 -> 当前前台: [{active_proc or '桌面/系统界面'}]")
                self.last_foreground_proc = active_proc

            # 策略评估与执行
            if matched_app:
                self._last_matched_app_id = matched_app.get("id")
                # 全局打开统计：任何情况下（管理器启动/外部双击/快捷方式/Steam）打开应用均精准统计
                if active_pid and active_pid > 0 and active_pid != os.getpid():
                    if active_pid not in self._tracked_running_pids:
                        self._tracked_running_pids.add(active_pid)
                        self.data_mgr.record_launch(matched_app["id"])
                        self.log(f"[打开统计] 识别到应用 [{matched_app['name']}] 启动运行 (PID: {active_pid})，已计入累计打开次数")

                app_name = matched_app["name"]
                tuning = self.data_mgr.get_effective_app_tuning(matched_app)
                gpu_mode = tuning.get("gpu_mode", "不修改")

                safe_min, safe_max, rule_desc = GPUService.validate_and_clamp_frequency(
                    gpu_mode,
                    freq=tuning.get("gpu_freq"),
                    min_freq=tuning.get("gpu_min_freq"),
                    max_freq=tuning.get("gpu_max_freq")
                )

                if self.active_app_name != app_name:
                    self.active_app_name = app_name
                    self.log(f"[策略确认] 应用 [{app_name}] 规则生效: {rule_desc}")

                auto_msi = settings.get("auto_launch_msi", True)
                if auto_msi and self.msi_service.is_installed() and not self.msi_service.is_running():
                    self.msi_service.launch_afterburner()

                # GPU 调频执行：仅在显卡可用且频率合法时执行，防止失控
                if safe_min is not None and safe_max is not None:
                    target_state = (safe_min, safe_max)
                    if self.current_locked_gpu_state != target_state:
                        if GPUService.is_gpu_available():
                            if sys.platform == "win32" and not is_admin():
                                self.log(f"[调频失败: 缺少管理员权限] 无法为应用 [{app_name}] 锁定频率为 {safe_min}-{safe_max} MHz！请以管理员权限重启启动器！")
                            else:
                                if use_buffer:
                                    GPUService.smooth_set_frequency(
                                        safe_min, safe_max, step_mhz=ramp_step, delay_step=ramp_delay, log_cb=self.log
                                    )
                                else:
                                    ok, msg = GPUService._direct_set_frequency(safe_min, safe_max)
                                    tag = "瞬时锁定成功" if ok else "锁定失败"
                                    self.log(f"[调频状态: {tag}] 范围: {safe_min}-{safe_max} MHz ({msg})")
                        else:
                            self.log(f"[调频拦截] 未检测到支持调控的 NVIDIA 显卡，拒绝下发 [{safe_min}-{safe_max} MHz]，防止频率失控")
                        self.current_locked_gpu_state = target_state
                else:
                    if self.current_locked_gpu_state is not None:
                        if GPUService.is_gpu_available() and is_admin():
                            GPUService.smooth_reset_frequency(step_mhz=ramp_step, delay_step=ramp_delay, log_cb=self.log)
                        self.current_locked_gpu_state = None
                        self.log(f"[调频状态: 释放锁定] 应用 [{app_name}] 设为不修改，维持常规调度")

                # 电源计划执行
                power_guid = tuning.get("power_plan_guid")
                if power_guid and power_guid != "默认":
                    if self.current_applied_power_plan != power_guid:
                        PowerPlanService.set_active_plan(power_guid)
                        self.current_applied_power_plan = power_guid
                        self.log(f"[系统电源: 切换成功] [{app_name}] -> 电源方案: {power_guid}")

                # MSI 曲线执行
                msi_prof = tuning.get("msi_profile")
                if msi_prof and msi_prof != "默认配置" and self.current_msi_profile != msi_prof:
                    p = self.msi_service.get_profile_by_name(msi_prof)
                    if p:
                        self.msi_service.apply_profile(p["id"])
                        self.current_msi_profile = msi_prof
                        self.log(f"[MSI联动: 预设载入] [{app_name}] -> Profile: {msi_prof}")

                self.update_status(f"运行中: {app_name} · {window_state_desc}", "#2563EB")
            else:
                self._last_matched_app_id = None
                # 失焦复位：仅在失焦防抖确认脱离目标后执行
                if self.current_locked_gpu_state is not None or (self.default_power_plan and self.current_applied_power_plan != self.default_power_plan):
                    self._restore_defaults()
                    self.log("[调频状态: 恢复默认] 焦点脱离目标应用，显卡频率与电源已安全归位")
                else:
                    self.update_status("监控运行中 (等待目标应用)", "#10B981")

            self._wake_event.wait(timeout=1.2)
            self._wake_event.clear()
