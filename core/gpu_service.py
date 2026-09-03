import re

def sanitize_text(text):
    if not text:
        return ""
    text = str(text).replace('\ufffd', '')
    text = re.sub(r'[\x00-\x1f\x7f-\x9f\u200b-\u200f\ufeff]', '', text)
    text = text.strip(' \t\r\n\u3000\u00a0')
    text = re.sub(r'[ \t\u3000\u00a0]+', ' ', text)
    return text

import ctypes
from ctypes import wintypes
import os
import shutil
import subprocess
import sys
import time
import threading

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    import pynvml
    HAS_NVML = True
except ImportError:
    HAS_NVML = False


def is_admin():
    if sys.platform == "win32":
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    return False


def elevate_privileges():
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
    """NVIDIA 显卡物理频率约束、动态探测与焦点状态识别服务"""

    MIN_HARDWARE_FREQ = 210
    DEFAULT_MAX_FREQ = 2500

    _nvml_initialized = False
    _gpu_handle = None
    _smi_path = None
    _target_gpu_index = "0"
    _gpu_name = "NVIDIA GPU"
    _gpu_detected = False
    _detected_max_freq = None

    _ramp_lock = threading.Lock()
    _cancel_ramp = threading.Event()
    _current_applied_freq = None
    _ramp_thread = None

    @classmethod
    def _get_smi_path(cls):
        if cls._smi_path:
            return cls._smi_path
        candidates = [
            shutil.which("nvidia-smi"),
            r"C:\Windows\System32\nvidia-smi.exe",
            r"C:\Program Files\NVIDIA Corporation\NVSMI\nvidia-smi.exe"
        ]
        for p in candidates:
            if p and os.path.exists(p):
                cls._smi_path = p
                return p
        cls._smi_path = "nvidia-smi"
        return cls._smi_path

    @classmethod
    def _init_nvml(cls):
        if not HAS_NVML:
            return False
        if cls._nvml_initialized and cls._gpu_handle:
            return True
        try:
            pynvml.nvmlInit()
            count = pynvml.nvmlDeviceGetCount()
            if count > 0:
                cls._gpu_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                cls._target_gpu_index = "0"
                try:
                    name_bytes = pynvml.nvmlDeviceGetName(cls._gpu_handle)
                    cls._gpu_name = name_bytes.decode('utf-8') if isinstance(name_bytes, bytes) else str(name_bytes)
                except Exception:
                    cls._gpu_name = "NVIDIA Graphics Device"
                cls._nvml_initialized = True
                cls._gpu_detected = True
                return True
        except Exception:
            cls._nvml_initialized = False
        return False

    @classmethod
    def detect_gpu_info(cls):
        """双通道显卡探针：优先 NVML，失败则回退至 nvidia-smi 命令行多卡扫描"""
        if cls._init_nvml():
            try:
                cur_clock = pynvml.nvmlDeviceGetClockInfo(cls._gpu_handle, pynvml.NVML_CLOCK_GRAPHICS)
                max_clock = pynvml.nvmlDeviceGetMaxClockInfo(cls._gpu_handle, pynvml.NVML_CLOCK_GRAPHICS)
                cls._detected_max_freq = max_clock if max_clock and max_clock > 500 else cls.DEFAULT_MAX_FREQ
                cls._gpu_detected = True
                return {
                    "available": True,
                    "name": cls._gpu_name,
                    "index": cls._target_gpu_index,
                    "current_freq": cur_clock,
                    "max_freq": cls._detected_max_freq
                }
            except Exception:
                pass

        # 回退至 nvidia-smi 命令行探测
        smi = cls._get_smi_path()
        try:
            cmd = [
                smi,
                "--query-gpu=index,name,clocks.current.graphics,clocks.max.graphics",
                "--format=csv,noheader,nounits"
            ]
            creation_flags = 0x08000000 if sys.platform == "win32" else 0
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=3, creationflags=creation_flags)
            if res.returncode == 0 and res.stdout.strip():
                lines = [line.strip() for line in res.stdout.strip().splitlines() if line.strip()]
                if lines:
                    first_gpu = [col.strip() for col in lines[0].split(",")]
                    if len(first_gpu) >= 2:
                        cls._target_gpu_index = first_gpu[0]
                        cls._gpu_name = first_gpu[1]
                        cls._gpu_detected = True
                        cur_f = int(first_gpu[2]) if len(first_gpu) > 2 and first_gpu[2].isdigit() else None
                        max_f = int(first_gpu[3]) if len(first_gpu) > 3 and first_gpu[3].isdigit() else cls.DEFAULT_MAX_FREQ
                        cls._detected_max_freq = max_f if max_f > 500 else cls.DEFAULT_MAX_FREQ
                        return {
                            "available": True,
                            "name": cls._gpu_name,
                            "index": cls._target_gpu_index,
                            "current_freq": cur_f,
                            "max_freq": cls._detected_max_freq
                        }
        except Exception:
            pass

        cls._gpu_detected = False
        return {
            "available": False,
            "name": "未检测到支持的 NVIDIA 显卡",
            "index": "0",
            "current_freq": None,
            "max_freq": cls.DEFAULT_MAX_FREQ
        }

    @classmethod
    def is_gpu_available(cls):
        info = cls.detect_gpu_info()
        return info["available"]

    @classmethod
    def get_max_safe_frequency(cls):
        if cls._detected_max_freq:
            return cls._detected_max_freq
        info = cls.detect_gpu_info()
        return info.get("max_freq") or cls.DEFAULT_MAX_FREQ

    @classmethod
    def get_current_frequency(cls):
        info = cls.detect_gpu_info()
        return info.get("current_freq")

    @classmethod
    def validate_and_clamp_frequency(cls, mode, freq=None, min_freq=None, max_freq=None):
        """严格校验规则，对不可用显卡实施拦截，防止输入溢出导致显卡失控降退或狂飙"""
        if not cls.is_gpu_available():
            return None, None, "未检测到可用 NVIDIA 显卡，跳过调频保护"

        hardware_max = cls.get_max_safe_frequency()
        hardware_min = cls.MIN_HARDWARE_FREQ

        if mode == "定频模式":
            try:
                target = int(freq) if freq is not None else 2000
            except (ValueError, TypeError):
                target = 2000
            safe_target = max(hardware_min, min(target, hardware_max))
            return safe_target, safe_target, f"定频锁定 {safe_target} MHz"

        elif mode == "频段模式":
            try:
                f_min = int(min_freq) if min_freq is not None else 210
            except (ValueError, TypeError):
                f_min = 210
            try:
                f_max = int(max_freq) if max_freq is not None else hardware_max
            except (ValueError, TypeError):
                f_max = hardware_max

            if f_min > f_max:
                f_min, f_max = f_max, f_min

            safe_min = max(hardware_min, min(f_min, hardware_max))
            safe_max = max(hardware_min, min(f_max, hardware_max))

            if safe_min == safe_max:
                return safe_min, safe_max, f"频段锁定已收敛至定频 {safe_min} MHz"
            return safe_min, safe_max, f"频段锁定 {safe_min}-{safe_max} MHz"

        return None, None, "默认策略 (不修改)"

    @classmethod
    def _direct_set_frequency(cls, min_freq, max_freq):
        if not cls.is_gpu_available():
            return False, "未检测到可用 NVIDIA 显卡设备"

        if sys.platform == "win32" and not is_admin():
            return False, "启动器未获取管理员权限，无法下发硬件锁频指令！请点击顶部按钮获取管理员权限"

        smi = cls._get_smi_path()
        gpu_idx = cls._target_gpu_index or "0"

        # 针对笔记本移动端显卡，若目标最大频率超过 2500 MHz 导致驱动拒绝，自动修正钳位
        hw_max = cls.get_max_safe_frequency()
        if "laptop" in cls._gpu_name.lower() or "mobile" in cls._gpu_name.lower():
            if max_freq > 2500 and hw_max > 2500:
                max_freq = min(max_freq, 2500)
                min_freq = min(min_freq, max_freq)

        try:
            cmd = [smi, "-i", str(gpu_idx), "-lgc", f"{min_freq},{max_freq}"]
            creation_flags = 0x08000000 if sys.platform == "win32" else 0
            result = subprocess.run(cmd, capture_output=True, text=True, creationflags=creation_flags)
            if result.returncode == 0:
                cls._current_applied_freq = (min_freq, max_freq)
                return True, f"锁定成功: {min_freq}-{max_freq} MHz (GPU {gpu_idx})"
            err = (result.stderr or result.stdout or "").strip()

            # 若因上限过高报错，尝试按安全步进降档重试一次
            if max_freq > 2000:
                fallback_max = 2000
                fallback_min = min(min_freq, fallback_max)
                retry_cmd = [smi, "-i", str(gpu_idx), "-lgc", f"{fallback_min},{fallback_max}"]
                r_res = subprocess.run(retry_cmd, capture_output=True, text=True, creationflags=creation_flags)
                if r_res.returncode == 0:
                    cls._current_applied_freq = (fallback_min, fallback_max)
                    return True, f"锁定成功(自适应降档): {fallback_min}-{fallback_max} MHz (GPU {gpu_idx})"

            cls._current_applied_freq = None
            return False, f"执行失败: {err}"
        except Exception as e:
            cls._current_applied_freq = None
            return False, f"调用异常: {str(e)}"

    @classmethod
    def smooth_set_frequency(cls, target_min, target_max, step_mhz=150, delay_step=0.035, log_cb=None):
        if not cls.is_gpu_available():
            if log_cb:
                log_cb("[调频警告] 未检测到可用 NVIDIA 显卡，取消调频")
            return False, "未检测到可用 NVIDIA 显卡"

        hardware_max = cls.get_max_safe_frequency()
        target_min = max(cls.MIN_HARDWARE_FREQ, min(int(target_min), hardware_max))
        target_max = max(cls.MIN_HARDWARE_FREQ, min(int(target_max), hardware_max))
        if target_min > target_max:
            target_min, target_max = target_max, target_min

        step_mhz = max(30, int(step_mhz))
        delay_step = max(0.01, float(delay_step))

        with cls._ramp_lock:
            cls._cancel_ramp.set()

            if cls._ramp_thread and cls._ramp_thread.is_alive():
                cls._ramp_thread.join(timeout=0.2)

            cls._cancel_ramp.clear()

            real_cur = cls.get_current_frequency()
            if cls._current_applied_freq:
                start_min, start_max = cls._current_applied_freq
            elif real_cur:
                start_min, start_max = real_cur, real_cur
            else:
                start_min, start_max = target_min, target_max

            def _ramp_worker():
                diff_min = target_min - start_min
                diff_max = target_max - start_max
                max_delta = max(abs(diff_min), abs(diff_max))

                if max_delta <= step_mhz:
                    ok, msg = cls._direct_set_frequency(target_min, target_max)
                    if log_cb:
                        log_cb(f"[调频状态: 锁定就绪] 目标: {target_min}-{target_max} MHz ({msg})")
                    return

                steps = int(max_delta / step_mhz) + 1
                if log_cb:
                    log_cb(f"[调频状态: 步进过渡中] 从 {start_min}-{start_max} MHz 渐变至 {target_min}-{target_max} MHz (分 {steps} 步, 步长 {step_mhz} MHz)")

                for i in range(1, steps + 1):
                    if cls._cancel_ramp.is_set():
                        return
                    cur_min = int(start_min + (diff_min * (i / steps)))
                    cur_max = int(start_max + (diff_max * (i / steps)))
                    ok, msg = cls._direct_set_frequency(cur_min, cur_max)
                    if not ok and log_cb:
                        log_cb(f"[调频警告: 步进失败] {msg}")
                    time.sleep(delay_step)

                if not cls._cancel_ramp.is_set():
                    ok, msg = cls._direct_set_frequency(target_min, target_max)
                    if log_cb:
                        tag = "锁定成功" if ok else "锁定被拒"
                        log_cb(f"[调频状态: {tag}] 稳态已配置至 {target_min}-{target_max} MHz ({msg})")

            cls._ramp_thread = threading.Thread(target=_ramp_worker, daemon=True)
            cls._ramp_thread.start()
            return True, f"平滑步进已启动 -> 目标: {target_min}-{target_max} MHz"

    @classmethod
    def reset_frequency(cls):
        with cls._ramp_lock:
            cls._cancel_ramp.set()

        if not cls.is_gpu_available():
            cls._current_applied_freq = None
            return True, "显卡不可用，跳过频率重置"

        if cls._current_applied_freq is None:
            return True, "当前无活动频率锁定，保持系统默认"

        smi = cls._get_smi_path()
        gpu_idx = cls._target_gpu_index or "0"
        try:
            cmd = [smi, "-i", str(gpu_idx), "-rgc"]
            creation_flags = 0x08000000 if sys.platform == "win32" else 0
            res = subprocess.run(cmd, capture_output=True, text=True, creationflags=creation_flags)
            cls._current_applied_freq = None
            if res.returncode == 0:
                return True, f"已恢复默认调频策略 (GPU {gpu_idx})"
            err = (res.stderr or res.stdout or "").strip()
            return False, f"恢复默认失败: {err}"
        except Exception as e:
            cls._current_applied_freq = None
            return False, str(e)

    @classmethod
    def smooth_reset_frequency(cls, step_mhz=150, delay_step=0.035, log_cb=None):
        if not cls.is_gpu_available():
            cls._current_applied_freq = None
            return True

        if cls._current_applied_freq:
            curr_min, curr_max = cls._current_applied_freq
            if curr_max > 1200:
                if log_cb:
                    log_cb(f"[调频状态: 安全缓冲回退] 正在平滑卸载当前高频锁定 ({curr_max} MHz)...")
                cls.smooth_set_frequency(300, 800, step_mhz=step_mhz, delay_step=delay_step)
                time.sleep(0.08)
        ok, msg = cls.reset_frequency()
        if log_cb:
            log_cb(f"[调频状态: 策略复位] {msg}")
        return ok

    @staticmethod
    def _get_process_name_by_pid(pid_val):
        if not pid_val or pid_val <= 0:
            return None

        try:
            kernel32 = ctypes.windll.kernel32
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            h_proc = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid_val)
            if h_proc:
                try:
                    buf = ctypes.create_unicode_buffer(1024)
                    size = wintypes.DWORD(1024)
                    if kernel32.QueryFullProcessImageNameW(h_proc, 0, buf, ctypes.byref(size)):
                        exe_path = buf.value
                        if exe_path:
                            return os.path.basename(exe_path)
                finally:
                    kernel32.CloseHandle(h_proc)
        except Exception:
            pass

        if HAS_PSUTIL:
            try:
                p = psutil.Process(pid_val)
                return p.name()
            except Exception:
                pass

        return None

    @classmethod
    def get_active_foreground_process_info(cls):
        """
        提取前台窗口核心三元组: (proc_name, pid_value, full_exe_path)
        1. 穿透至根拥有者窗口 (GA_ROOTOWNER)
        2. 穿透 Windows UWP ApplicationFrameHost 获取内部真实子窗口进程
        3. 若焦点在本管理器自身窗口，返回 ('__SELF__', os.getpid(), sys.executable)
        """
        if sys.platform != "win32":
            return None, None, None

        try:
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            if not hwnd or not user32.IsWindow(hwnd) or not user32.IsWindowVisible(hwnd):
                return None, None, None

            GA_ROOTOWNER = 3
            hwnd_root = user32.GetAncestor(hwnd, GA_ROOTOWNER)
            if hwnd_root and user32.IsWindow(hwnd_root):
                hwnd = hwnd_root

            cls_name = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, cls_name, 256)
            class_val = cls_name.value
            if class_val in ("Progman", "WorkerW", "Shell_TrayWnd", "Windows.UI.Core.CoreWindow"):
                return None, None, None

            pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value <= 0:
                return None, None, None

            if pid.value == os.getpid():
                return "__SELF__", pid.value, sys.executable

            full_path = None
            proc_name = None

            # 优先通过 Win32 API 提取完整路径与名称 (突破反作弊权限限制)
            try:
                kernel32 = ctypes.windll.kernel32
                PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
                h_proc = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
                if h_proc:
                    try:
                        buf = ctypes.create_unicode_buffer(1024)
                        size = wintypes.DWORD(1024)
                        if kernel32.QueryFullProcessImageNameW(h_proc, 0, buf, ctypes.byref(size)):
                            full_path = buf.value
                            if full_path:
                                proc_name = os.path.basename(full_path)
                    finally:
                        kernel32.CloseHandle(h_proc)
            except Exception:
                pass

            if not proc_name and HAS_PSUTIL:
                try:
                    p = psutil.Process(pid.value)
                    proc_name = p.name()
                    full_path = p.exe()
                except Exception:
                    pass

            if not proc_name:
                return None, None, None

            # 过滤 Windows 桌面外壳 (Program Manager / Desktop)
            if proc_name.lower() == "explorer.exe":
                w_len = user32.GetWindowTextLengthW(hwnd)
                if w_len > 0:
                    w_buf = ctypes.create_unicode_buffer(w_len + 1)
                    user32.GetWindowTextW(hwnd, w_buf, w_len + 1)
                    w_title = w_buf.value.strip().lower()
                    if w_title in ("program manager", "desktop", "桌面"):
                        return None, None, None

            # 若前台属于 UWP 托管容器 ApplicationFrameHost.exe，枚举其子窗口找到实际业务进程
            if proc_name.lower() == "applicationframehost.exe":
                real_pid = ctypes.c_ulong(0)

                def enum_child_proc(chwnd, lParam):
                    nonlocal real_pid
                    c_pid = ctypes.c_ulong()
                    user32.GetWindowThreadProcessId(chwnd, ctypes.byref(c_pid))
                    if c_pid.value > 0 and c_pid.value != pid.value:
                        c_name = cls._get_process_name_by_pid(c_pid.value)
                        if c_name and c_name.lower() != "applicationframehost.exe":
                            real_pid.value = c_pid.value
                            return False
                    return True

                EnumChildProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
                user32.EnumChildWindows(hwnd, EnumChildProc(enum_child_proc), 0)
                if real_pid.value > 0:
                    real_name = cls._get_process_name_by_pid(real_pid.value)
                    if real_name:
                        return real_name, real_pid.value, None

            return proc_name, pid.value, full_path
        except Exception:
            return None, None, None

    @classmethod
    def get_active_foreground_process_name(cls):
        name, _, _ = cls.get_active_foreground_process_info()
        return name

    @classmethod
    def capture_foreground_app_info(cls, delay_seconds=0):
        if sys.platform != "win32":
            return None

        if delay_seconds > 0:
            time.sleep(delay_seconds)

        try:
            user32 = ctypes.windll.user32
            current_pid = os.getpid()
            target_hwnd = None
            target_pid = None

            if delay_seconds > 0:
                hwnd = user32.GetForegroundWindow()
                if hwnd and user32.IsWindowVisible(hwnd):
                    pid = ctypes.c_ulong()
                    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                    if pid.value > 0 and pid.value != current_pid:
                        target_hwnd = hwnd
                        target_pid = pid.value
            else:
                def enum_windows_proc(hwnd, lParam):
                    nonlocal target_hwnd, target_pid
                    if user32.IsWindowVisible(hwnd):
                        length = user32.GetWindowTextLengthW(hwnd)
                        if length > 0:
                            pid = ctypes.c_ulong()
                            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                            if pid.value > 0 and pid.value != current_pid:
                                target_hwnd = hwnd
                                target_pid = pid.value
                                return False
                    return True

                EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
                user32.EnumWindows(EnumWindowsProc(enum_windows_proc), 0)

            if target_pid:
                exe_name = cls._get_process_name_by_pid(target_pid) or f"Process_{target_pid}.exe"
                exe_path = ""
                if HAS_PSUTIL:
                    try:
                        proc = psutil.Process(target_pid)
                        exe_path = proc.exe()
                        exe_name = proc.name()
                    except Exception:
                        pass

                length = user32.GetWindowTextLengthW(target_hwnd)
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(target_hwnd, buff, length + 1)
                win_title = sanitize_text(buff.value)
                display_name = sanitize_text(win_title) if (win_title and len(win_title) < 40) else sanitize_text(os.path.splitext(exe_name)[0])

                return {
                    "pid": target_pid,
                    "name": display_name,
                    "exe_name": exe_name,
                    "exe_path": os.path.normpath(exe_path) if exe_path else exe_name
                }
        except Exception:
            return None
        return None
