import os
import re
import shutil
import subprocess
import sys

if sys.platform == "win32":
    import winreg
else:
    winreg = None


class AppScanner:
    """Windows 控制面板已安装应用程序扫描器"""

    @classmethod
    def get_installed_apps(cls):
        apps = []
        seen_names = set()

        if winreg:
            apps = cls._scan_registry()

        if len(apps) < 3 and sys.platform == "win32":
            ps_apps = cls._scan_powershell()
            for app in ps_apps:
                key = app["name"].lower()
                if key not in seen_names:
                    seen_names.add(key)
                    apps.append(app)

        return sorted(apps, key=lambda x: x["name"].lower())

    @classmethod
    def _scan_registry(cls):
        apps = []
        seen_names = set()

        sub_path_1 = "SOFTWARE/Microsoft/Windows/CurrentVersion/Uninstall"
        sub_path_2 = "SOFTWARE/WOW6432Node/Microsoft/Windows/CurrentVersion/Uninstall"
        sub_path_3 = "Software/Microsoft/Windows/CurrentVersion/Uninstall"

        targets = [
            (winreg.HKEY_LOCAL_MACHINE, sub_path_1, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) if winreg else None,
            (winreg.HKEY_LOCAL_MACHINE, sub_path_1, winreg.KEY_READ | winreg.KEY_WOW64_32KEY) if winreg else None,
            (winreg.HKEY_LOCAL_MACHINE, sub_path_2, winreg.KEY_READ | winreg.KEY_WOW64_32KEY) if winreg else None,
            (winreg.HKEY_CURRENT_USER, sub_path_3, winreg.KEY_READ) if winreg else None,
        ]

        for target in targets:
            if not target:
                continue
            hkey, subkey_path, access_flag = target
            try:
                key = winreg.OpenKey(hkey, subkey_path, 0, access_flag)
                num_subkeys, _, _ = winreg.QueryInfoKey(key)

                for i in range(num_subkeys):
                    try:
                        sub_name = winreg.EnumKey(key, i)
                        sub_key = winreg.OpenKey(key, sub_name, 0, access_flag)

                        system_comp = cls._get_reg_val(sub_key, "SystemComponent")
                        parent_key = cls._get_reg_val(sub_key, "ParentKeyName")
                        if system_comp == 1 or parent_key:
                            continue

                        display_name = cls._get_reg_val(sub_key, "DisplayName")
                        if not display_name or isinstance(display_name, int):
                            continue

                        display_name = str(display_name).strip()
                        if not display_name or display_name.lower() in seen_names:
                            continue

                        display_icon = str(cls._get_reg_val(sub_key, "DisplayIcon") or "")
                        install_dir = str(cls._get_reg_val(sub_key, "InstallLocation") or "")
                        uninstall_str = str(cls._get_reg_val(sub_key, "UninstallString") or "")

                        exe_path, exe_name = cls._resolve_executable(
                            display_name, display_icon, install_dir, uninstall_str
                        )

                        seen_names.add(display_name.lower())
                        apps.append({
                            "name": display_name,
                            "exe_name": exe_name if exe_name else (display_name + ".exe"),
                            "exe_path": exe_path
                        })
                    except Exception:
                        pass
            except Exception:
                pass

        return apps

    @staticmethod
    def _get_reg_val(key, val_name):
        try:
            val, _ = winreg.QueryValueEx(key, val_name)
            return val
        except Exception:
            return None

    @classmethod
    def _resolve_executable(cls, display_name, display_icon, install_dir, uninstall_str):
        exe_path = ""
        if display_icon:
            icon_path = display_icon.split(",")[0].strip('"').strip()
            icon_path = os.path.expandvars(icon_path)
            if os.path.exists(icon_path):
                exe_path = icon_path

        possible_exe_names = [f"{display_name}.exe", f"{display_name.replace(' ', '')}.exe"]
        if display_icon and (display_icon.lower().endswith(".exe") or ".exe," in display_icon.lower()):
            icon_base = os.path.basename(display_icon.split(",")[0].strip('"').strip())
            if icon_base and icon_base not in possible_exe_names:
                possible_exe_names.insert(0, icon_base)

        if not exe_path and winreg:
            for name_cand in possible_exe_names:
                for root_key in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
                    app_path_key = f"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\{name_cand}"
                    try:
                        with winreg.OpenKey(root_key, app_path_key) as k:
                            p_val = cls._get_reg_val(k, "")
                            if p_val:
                                p_val = os.path.expandvars(str(p_val).strip('"').strip())
                                if os.path.exists(p_val):
                                    exe_path = p_val
                                    break
                    except Exception:
                        pass
                if exe_path:
                    break

        if not exe_path and install_dir:
            clean_dir = os.path.expandvars(install_dir.strip('"').strip())
            if os.path.exists(clean_dir):
                try:
                    exe_candidates = []
                    for root_dir, _, files in os.walk(clean_dir):
                        for f in files:
                            if f.lower().endswith(".exe") and "unins" not in f.lower() and "setup" not in f.lower():
                                exe_candidates.append(os.path.join(root_dir, f))
                    if exe_candidates:
                        exe_candidates.sort(key=lambda p: (p.count(os.sep), -os.path.getsize(p) if os.path.exists(p) else 0))
                        exe_path = exe_candidates[0]
                except Exception:
                    pass

        if not exe_path:
            for cand in possible_exe_names:
                found = shutil.which(cand)
                if found and os.path.exists(found):
                    exe_path = found
                    break

        exe_name = os.path.basename(exe_path) if exe_path else (possible_exe_names[0] if possible_exe_names else "")
        return exe_path, exe_name

    @classmethod
    def _scan_powershell(cls):
        apps = []
        try:
            cmd = (
                "Get-ItemProperty "
                "HKLM:/Software/Microsoft/Windows/CurrentVersion/Uninstall/*, "
                "HKLM:/Software/Wow6432Node/Microsoft/Windows/CurrentVersion/Uninstall/*, "
                "HKCU:/Software/Microsoft/Windows/CurrentVersion/Uninstall/* "
                "| Where-Object { $_.DisplayName -and -not $_.SystemComponent } "
                "| Select-Object DisplayName, DisplayIcon, InstallLocation, UninstallString "
                "| ConvertTo-Json"
            )
            creation_flags = 0x08000000 if sys.platform == "win32" else 0
            res = subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True, timeout=8, creationflags=creation_flags)
            if res.returncode == 0 and res.stdout.strip():
                import json
                data = json.loads(res.stdout)
                if isinstance(data, dict):
                    data = [data]
                for item in data:
                    name = str(item.get("DisplayName") or "").strip()
                    if not name:
                        continue
                    icon = str(item.get("DisplayIcon") or "")
                    dir_path = str(item.get("InstallLocation") or "")
                    unins = str(item.get("UninstallString") or "")
                    exe_path, exe_name = cls._resolve_executable(name, icon, dir_path, unins)
                    apps.append({
                        "name": name,
                        "exe_name": exe_name if exe_name else (name + ".exe"),
                        "exe_path": exe_path
                    })
        except Exception:
            pass
        return apps
