import os
import re
import winreg


class MSIFinder:
    """负责查找微星小飞机的安装路径"""

    @classmethod
    def find_install_path(cls) -> str | None:
        path = cls._find_from_registry()
        if path:
            return path

        path = cls._find_from_app_scanner()
        if path:
            return path

        path = cls._find_from_common_paths()
        if path:
            return path

        return None

    @classmethod
    def _find_from_registry(cls) -> str | None:
        try:
            uninstall_paths = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\MSI Afterburner"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\MSI Afterburner"),
            ]

            for hkey, subkey in uninstall_paths:
                try:
                    with winreg.OpenKey(hkey, subkey) as key:
                        install_location = cls._get_reg_val(key, "InstallLocation")
                        if install_location and os.path.exists(install_location):
                            exe_path = os.path.join(install_location, "MSIAfterburner.exe")
                            if os.path.exists(exe_path):
                                return install_location

                        display_icon = cls._get_reg_val(key, "DisplayIcon")
                        if display_icon:
                            exe_path = display_icon.split(',')[0].strip('"')
                            if os.path.exists(exe_path):
                                return os.path.dirname(exe_path)

                        uninstall_string = cls._get_reg_val(key, "UninstallString")
                        if uninstall_string:
                            match = re.search(r'"([^"]+MSIAfterburner[^"]*\.exe)"', uninstall_string, re.IGNORECASE)
                            if match:
                                exe_path = match.group(1)
                                if os.path.exists(exe_path):
                                    return os.path.dirname(exe_path)
                except (FileNotFoundError, PermissionError, OSError):
                    continue

            app_paths = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\MSIAfterburner.exe"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths\MSIAfterburner.exe"),
            ]

            for hkey, subkey in app_paths:
                try:
                    with winreg.OpenKey(hkey, subkey) as key:
                        exe_path = cls._get_reg_val(key, "")
                        if exe_path and os.path.exists(exe_path):
                            return os.path.dirname(exe_path)
                except (FileNotFoundError, PermissionError, OSError):
                    continue

        except Exception:
            pass

        return None

    @classmethod
    def _find_from_app_scanner(cls) -> str | None:
        try:
            from app_scanner import AppScanner
            apps = AppScanner.get_installed_apps()

            for app in apps:
                name = app.get("name", "").lower()
                if "msi afterburner" in name or "afterburner" in name:
                    exe_path = app.get("exe_path", "")
                    if exe_path and os.path.exists(exe_path):
                        install_dir = os.path.dirname(exe_path)
                        if os.path.exists(os.path.join(install_dir, "MSIAfterburner.exe")):
                            return install_dir

                    install_dir = app.get("install_dir", "")
                    if install_dir and os.path.exists(install_dir):
                        exe_path = os.path.join(install_dir, "MSIAfterburner.exe")
                        if os.path.exists(exe_path):
                            return install_dir

        except Exception:
            pass

        return None

    @classmethod
    def _find_from_common_paths(cls) -> str | None:
        possible_paths = [
            r"C:\Program Files (x86)\MSI Afterburner",
            r"C:\Program Files\MSI Afterburner",
            os.path.expandvars(r"%PROGRAMFILES(x86)%\MSI Afterburner"),
            os.path.expandvars(r"%PROGRAMFILES%\MSI Afterburner"),
            os.path.expandvars(r"%LOCALAPPDATA%\MSI Afterburner"),
        ]

        for path in possible_paths:
            if path and os.path.exists(path):
                exe_path = os.path.join(path, "MSIAfterburner.exe")
                if os.path.exists(exe_path):
                    return path

        return None

    @staticmethod
    def _get_reg_val(key, val_name):
        try:
            val, _ = winreg.QueryValueEx(key, val_name)
            return val
        except Exception:
            return None