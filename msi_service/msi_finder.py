import sys
import os
import re
if sys.platform == "win32":
    import winreg
else:
    winreg = None


class MSIFinder:
    @classmethod
    def find_install_path(cls) -> str | None:
        path = cls._find_from_registry()
        if path:
            return path
        return cls._find_from_common_paths()

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
                except Exception:
                    continue
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
