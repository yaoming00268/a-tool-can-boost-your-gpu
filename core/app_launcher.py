import os
import sys
import ctypes
from ctypes import wintypes
import subprocess

if sys.platform == "win32":
    import winreg
else:
    winreg = None

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from core.icon_helper import IconHelper


def _launch_unprivileged_win32(exe_path, env_dict=None, cwd=None):
    """
    通过 Windows COM (Shell.Application) 或复制 Explorer 令牌，
    以标准用户（Medium Integrity）权限启动子应用。
    彻底去除子程序继承管理器的 Administrator 权限，确保启动器自身保持管理员权限
    而子程序作为普通用户运行。
    """
    # 策略 1: 尝试通过 Explorer 令牌复制降权
    try:
        user32 = ctypes.windll.user32
        advapi32 = ctypes.windll.advapi32
        kernel32 = ctypes.windll.kernel32

        shell_hwnd = user32.GetShellWindow()
        if shell_hwnd:
            shell_pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(shell_hwnd, ctypes.byref(shell_pid))
            if shell_pid.value > 0:
                PROCESS_QUERY_INFORMATION = 0x0400
                h_process = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION, False, shell_pid.value)
                if h_process:
                    try:
                        TOKEN_DUPLICATE = 0x0002
                        TOKEN_QUERY = 0x0008
                        TOKEN_ASSIGN_PRIMARY = 0x0001
                        h_token = wintypes.HANDLE()
                        if advapi32.OpenProcessToken(
                            h_process, TOKEN_DUPLICATE | TOKEN_QUERY | TOKEN_ASSIGN_PRIMARY, ctypes.byref(h_token)
                        ):
                            try:
                                TOKEN_ALL_ACCESS = 0xF01FF
                                SecurityImpersonation = 2
                                TokenPrimary = 1
                                h_new_token = wintypes.HANDLE()
                                if advapi32.DuplicateTokenEx(
                                    h_token, TOKEN_ALL_ACCESS, None, SecurityImpersonation, TokenPrimary, ctypes.byref(h_new_token)
                                ):
                                    try:
                                        env_block = None
                                        if env_dict:
                                            env_str = ""
                                            for k, v in env_dict.items():
                                                env_str += f"{k}={v}\0"
                                            env_str += "\0"
                                            env_block = ctypes.c_wchar_p(env_str)

                                        class STARTUPINFOW(ctypes.Structure):
                                            _fields_ = [
                                                ('cb', wintypes.DWORD),
                                                ('lpReserved', wintypes.LPWSTR),
                                                ('lpDesktop', wintypes.LPWSTR),
                                                ('lpTitle', wintypes.LPWSTR),
                                                ('dwX', wintypes.DWORD),
                                                ('dwY', wintypes.DWORD),
                                                ('dwXSize', wintypes.DWORD),
                                                ('dwYSize', wintypes.DWORD),
                                                ('dwXCountChars', wintypes.DWORD),
                                                ('dwYCountChars', wintypes.DWORD),
                                                ('dwFillAttribute', wintypes.DWORD),
                                                ('dwFlags', wintypes.DWORD),
                                                ('wShowWindow', wintypes.WORD),
                                                ('cbReserved2', wintypes.WORD),
                                                ('lpReserved2', ctypes.c_char_p),
                                                ('hStdInput', wintypes.HANDLE),
                                                ('hStdOutput', wintypes.HANDLE),
                                                ('hStdError', wintypes.HANDLE),
                                            ]

                                        class PROCESS_INFORMATION(ctypes.Structure):
                                            _fields_ = [
                                                ('hProcess', wintypes.HANDLE),
                                                ('hThread', wintypes.HANDLE),
                                                ('dwProcessId', wintypes.DWORD),
                                                ('dwThreadId', wintypes.DWORD),
                                            ]

                                        si = STARTUPINFOW()
                                        si.cb = ctypes.sizeof(STARTUPINFOW)
                                        pi = PROCESS_INFORMATION()

                                        CREATE_UNICODE_ENVIRONMENT = 0x00000400
                                        creation_flags = CREATE_UNICODE_ENVIRONMENT if env_block else 0
                                        work_dir = os.path.abspath(cwd) if cwd else os.path.dirname(os.path.abspath(exe_path))
                                        cmd_line = f'"{os.path.abspath(exe_path)}"'

                                        ok = advapi32.CreateProcessWithTokenW(
                                            h_new_token,
                                            0,
                                            None,
                                            cmd_line,
                                            creation_flags,
                                            env_block,
                                            work_dir,
                                            ctypes.byref(si),
                                            ctypes.byref(pi)
                                        )

                                        if ok:
                                            pid = pi.dwProcessId
                                            kernel32.CloseHandle(pi.hProcess)
                                            kernel32.CloseHandle(pi.hThread)
                                            return pid, "成功以普通用户令牌启动程序"
                                    finally:
                                        kernel32.CloseHandle(h_new_token)
                            finally:
                                kernel32.CloseHandle(h_token)
                    finally:
                        kernel32.CloseHandle(h_process)
    except Exception:
        pass

    # 策略 2: 降权启动备选：利用 Explorer 执行命令行启动（子进程归属于标准权限 Explorer）
    try:
        abs_exe = os.path.abspath(exe_path)
        # 通过 explorer.exe 直接启动，使新程序运行在当前用户的普通权限下
        creation_flags = 0x08000000 if sys.platform == "win32" else 0
        proc = subprocess.Popen(f'explorer.exe "{abs_exe}"', shell=True, creationflags=creation_flags)
        return proc.pid, "通过 Explorer 标准用户外壳启动"
    except Exception:
        pass

    return None, "降权启动回退至常规启动"


class AppLauncher:
    """应用程序启动、降权启动隔离、代理注入与进程终止管理器"""

    _launched_pids = set()
    _launched_exe_names = set()
    _pid_to_app_id = {}          # PID 到具体 app_id 的映射，保证多应用重名精准匹配
    _last_launched_app_id = None  # 最近通过启动器启动的应用 ID

    @classmethod
    def launch_app(cls, exe_path_or_name, app_id=None, proxy_url=""):
        path = IconHelper.resolve_path(exe_path_or_name)
        if not path or not os.path.exists(path):
            return False, f"未找到程序路径: {exe_path_or_name}"

        try:
            env = os.environ.copy()
            if proxy_url and proxy_url.strip():
                p = proxy_url.strip()
                env["HTTP_PROXY"] = p
                env["HTTPS_PROXY"] = p
                env["ALL_PROXY"] = p
                env["http_proxy"] = p
                env["https_proxy"] = p
                env["all_proxy"] = p

            app_dir = os.path.dirname(path)
            pid = None

            # 若为 Windows 系统，执行标准用户降权启动（确保启动器自身为管理员，子应用为普通用户）
            if sys.platform == "win32":
                pid, _ = _launch_unprivileged_win32(path, env_dict=env, cwd=app_dir)

            # 若降权失败或非 Windows 环境，使用标准启动
            if not pid:
                creation_flags = 0x08000000 if sys.platform == "win32" else 0
                proc = subprocess.Popen([path], env=env, cwd=app_dir, creationflags=creation_flags)
                pid = proc.pid

            if pid:
                cls._launched_pids.add(pid)
                if app_id:
                    cls._pid_to_app_id[pid] = app_id
                    cls._last_launched_app_id = app_id

            cls._launched_exe_names.add(os.path.basename(path).lower())

            proxy_msg = f" (已挂载代理: {proxy_url})" if proxy_url else ""
            return True, f"已成功启动程序(标准用户权限): {os.path.basename(path)}{proxy_msg}"
        except Exception as e:
            return False, f"程序启动失败: {str(e)}"

    @classmethod
    def get_app_id_by_pid(cls, pid):
        """通过进程 PID 直接检索启动的应用 ID"""
        if not pid:
            return None
        return cls._pid_to_app_id.get(pid)

    @classmethod
    def get_last_launched_app_id(cls):
        return cls._last_launched_app_id

    @classmethod
    def is_process_launched_by_manager(cls, process_name, pid=None):
        if pid and pid in cls._launched_pids:
            return True
        p_clean = (process_name or "").strip().lower()
        if p_clean in cls._launched_exe_names:
            return True
        if HAS_PSUTIL:
            for p in psutil.process_iter(['name']):
                try:
                    if p.info['name'] and p.info['name'].lower() == p_clean:
                        return True
                except Exception:
                    pass
        return False

    @classmethod
    def terminate_app(cls, process_name):
        if not process_name:
            return False, "进程名为空"
        p_lower = process_name.strip().lower()
        killed_count = 0
        try:
            if HAS_PSUTIL:
                for p in psutil.process_iter(['pid', 'name']):
                    try:
                        if p.info['name'] and p.info['name'].lower() == p_lower:
                            pid_val = p.info['pid']
                            cls._launched_pids.discard(pid_val)
                            cls._pid_to_app_id.pop(pid_val, None)
                            p.kill()
                            killed_count += 1
                    except Exception:
                        pass
            cls._launched_exe_names.discard(p_lower)
            if killed_count > 0:
                return True, f"已成功终止 {killed_count} 个 [{process_name}] 进程实例"
            return False, f"未检测到 [{process_name}] 正在运行"
        except Exception as e:
            return False, f"终止进程异常: {str(e)}"

    @staticmethod
    def set_app_autostart(app_name, exe_path, enable=True):
        if sys.platform != "win32" or not exe_path or not winreg:
            return False
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        reg_key_name = f"NanakoApp_{app_name.replace(' ', '_')}"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
            if enable:
                winreg.SetValueEx(key, reg_key_name, 0, winreg.REG_SZ, f'"{os.path.abspath(exe_path)}"')
            else:
                try:
                    winreg.DeleteValue(key, reg_key_name)
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
            return True
        except Exception:
            return False
