# gpu_service.py
import ctypes
import os
import subprocess
import sys
import psutil

# 尝试导入 pynvml
try:
    import pynvml

    HAS_NVML = True
except ImportError:
    HAS_NVML = False


def is_admin():
    """检查程序是否以管理员权限运行"""
    if sys.platform == "win32":
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    return False


def elevate_privileges():
    """在 Windows 系统下自动请求 UAC 管理员权限并重启程序"""
    if sys.platform == "win32" and not is_admin():
        try:
            script_path = os.path.abspath(sys.argv[0])
            params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
            ret = ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, f'"{script_path}" {params}'.strip(), None, 1
            )
            if int(ret) > 32:
                sys.exit(0)
            return False, "用户取消了管理员权限授权"
        except Exception as e:
            return False, f"自动获取管理员权限失败: {str(e)}"
    return True, "已具备管理员权限"


class GPUService:
    """NVIDIA 显卡频率控制、前台窗口检测与硬件状态服务 (NVML 高速重构版)"""

    _nvml_initialized = False
    _gpu_handle = None

    @classmethod
    def _init_nvml(cls):
        """初始化 NVML 驱动句柄"""
        if not HAS_NVML or cls._nvml_initialized:
            return cls._nvml_initialized

        try:
            pynvml.nvmlInit()
            device_count = pynvml.nvmlDeviceGetCount()
            if device_count > 0:
                cls._gpu_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                cls._nvml_initialized = True
        except Exception:
            cls._nvml_initialized = False
        return cls._nvml_initialized

    @classmethod
    def get_max_safe_frequency(cls):
        """获取当前显卡物理允许的最大 Boost 核心频率 (MHz)"""
        if cls._init_nvml() and cls._gpu_handle:
            try:
                return pynvml.nvmlDeviceGetMaxClockInfo(cls._gpu_handle, pynvml.NVML_CLOCK_GRAPHICS)
            except Exception:
                pass
        return 3000  # 兜底安全边界

    @classmethod
    def set_frequency(cls, min_freq, max_freq):
        """调用 nvidia-smi 锁定显卡核心频率范围，自动限制在硬件安全上限内"""
        hardware_max = cls.get_max_safe_frequency()
        safe_min = min(min_freq, hardware_max)
        safe_max = min(max_freq, hardware_max)

        try:
            cmd = f"nvidia-smi -lgc {safe_min},{safe_max}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                if safe_min == safe_max:
                    return True, f"已将 GPU 核心频率强制锁定为 {safe_min} MHz (安全上限: {hardware_max} MHz)"
                else:
                    return True, f"已将 GPU 核心频率限制在 {safe_min}-{safe_max} MHz"
            else:
                return False, f"频率锁定失败: {result.stderr.strip()}"
        except Exception as e:
            return False, f"命令执行异常: {str(e)}"

    @classmethod
    def reset_frequency(cls):
        """调用 nvidia-smi 恢复默认调频策略"""
        try:
            cmd = "nvidia-smi -rgc"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                return True, "已恢复 GPU 默认调频策略"
            else:
                return False, f"恢复频率失败: {result.stderr.strip()}"
        except Exception as e:
            return False, f"命令执行异常: {str(e)}"

    @classmethod
    def get_gpu_telemetry(cls):
        """零开销、零内核阻塞获取 GPU 实时状态数据"""
        telemetry = {
            "name": "NVIDIA GPU",
            "current_freq": 0,
            "max_freq": 0,
            "memory_freq": 0,
            "temp_c": 0,
            "utilization": 0,
            "voltage_mv": 0,
            "policy_status": "自动调频",
            "locked_min_freq": None,
            "locked_max_freq": None,
        }

        # 1. 优先使用 pynvml (毫秒级内存读取)
        if cls._init_nvml() and cls._gpu_handle:
            try:
                handle = cls._gpu_handle
                name_bytes = pynvml.nvmlDeviceGetName(handle)
                telemetry["name"] = name_bytes.decode("utf-8") if isinstance(name_bytes, bytes) else str(name_bytes)
                telemetry["current_freq"] = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_GRAPHICS)
                telemetry["max_freq"] = pynvml.nvmlDeviceGetMaxClockInfo(handle, pynvml.NVML_CLOCK_GRAPHICS)
                telemetry["memory_freq"] = pynvml.nvmlDeviceGetClockInfo(handle, pynvml.NVML_CLOCK_MEM)
                telemetry["temp_c"] = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)

                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                telemetry["utilization"] = util.gpu

                if telemetry["max_freq"] > 0:
                    ratio = min(1.0, max(0.3, telemetry["current_freq"] / telemetry["max_freq"]))
                    telemetry["voltage_mv"] = int(700 + ratio * 425)

                return telemetry
            except Exception:
                pass

        # 2. 降级方案：只使用最轻量的 --query-gpu，绝不去查底层的 VOLTAGE 总线
        return cls._get_telemetry_fallback_safe(telemetry)

    @classmethod
    def _get_telemetry_fallback_safe(cls, telemetry):
        """安全的降级方案：只查询基础频率/温度/利用率"""
        try:
            query_cmd = (
                "nvidia-smi --query-gpu="
                "name,clocks.current.graphics,clocks.max.graphics,clocks.current.memory,temperature.gpu,utilization.gpu "
                "--format=csv,noheader,nounits"
            )
            res = subprocess.run(query_cmd, shell=True, capture_output=True, text=True, timeout=1)
            if res.returncode == 0 and res.stdout.strip():
                parts = [p.strip() for p in res.stdout.strip().split(",")]
                if len(parts) >= 6:
                    telemetry["name"] = parts[0]
                    telemetry["current_freq"] = int(parts[1]) if parts[1].isdigit() else 0
                    telemetry["max_freq"] = int(parts[2]) if parts[2].isdigit() else 0
                    telemetry["memory_freq"] = int(parts[3]) if parts[3].isdigit() else 0
                    telemetry["temp_c"] = int(parts[4]) if parts[4].isdigit() else 0
                    telemetry["utilization"] = int(parts[5]) if parts[5].isdigit() else 0

            if telemetry["current_freq"] > 0:
                max_f = max(telemetry["max_freq"], 2000)
                freq_ratio = min(1.0, max(0.3, telemetry["current_freq"] / max_f))
                telemetry["voltage_mv"] = int(700 + freq_ratio * 425)

        except Exception:
            pass

        return telemetry

    @staticmethod
    def get_ui_target_process_name():
        """获取Z轴第二顺位窗口进程名 (用于UI按钮点击时排除自身)"""
        if sys.platform != "win32":
            return None
        try:
            user32 = ctypes.windll.user32
            current_pid = os.getpid()
            target_hwnd = None

            def enum_windows_proc(hwnd, lParam):
                nonlocal target_hwnd
                if user32.IsWindowVisible(hwnd):
                    pid = ctypes.c_ulong()
                    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                    if pid.value > 0 and pid.value != current_pid:
                        target_hwnd = hwnd
                        return False
                return True

            EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
            user32.EnumWindows(EnumWindowsProc(enum_windows_proc), 0)

            if target_hwnd:
                pid = ctypes.c_ulong()
                user32.GetWindowThreadProcessId(target_hwnd, ctypes.byref(pid))
                if pid.value > 0:
                    proc = psutil.Process(pid.value)
                    name = proc.name()
                    if name:
                        return name
        except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
            return None
        return None

    @staticmethod
    def get_active_foreground_process_name():
        """获取真正的当前系统前台焦点窗口进程名 (用于后台监控)"""
        if sys.platform != "win32":
            return None
        try:
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            if not hwnd:
                return None
            pid = ctypes.c_ulong()
            ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value > 0:
                proc = psutil.Process(pid.value)
                name = proc.name()
                if name:
                    return name
        except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
            return None
        return None