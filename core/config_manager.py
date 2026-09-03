import json
import os
import sys
if sys.platform == "win32":
    import winreg
else:
    winreg = None


class ConfigManager:
    """配置文件管理器"""

    DEFAULT_FILE = "gpu_booster_config.json"

    def __init__(self, config_file=DEFAULT_FILE):
        self.config_file = config_file
        self.data = self.load_config()

    def load_config(self):
        default_structure = {
            "active_profile": "默认配置",
            "only_foreground": True,
            "settings": {
                "auto_start": False,
                "auto_profile": "不自动启用",
                "hotkey": "F12"
            },
            "profiles": {
                "默认配置": []
            }
        }
        if not os.path.exists(self.config_file):
            return default_structure

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "profiles" not in data: data["profiles"] = {"默认配置": []}
                if "settings" not in data: data["settings"] = default_structure["settings"]
                return data
        except Exception:
            return default_structure

    def save_config(self):
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            return True, "配置保存成功"
        except Exception as e:
            return False, f"保存失败: {str(e)}"

    def get_settings(self):
        return self.data.get("settings", {})

    def save_settings(self, settings):
        self.data["settings"] = settings
        self.save_config()
        self.apply_auto_start(settings.get("auto_start", False))
        return True

    def apply_auto_start(self, enable):
        """写入 Windows 注册表实现开机自启"""
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "GPUFrequencyBooster"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
            if enable:
                exe_path = os.path.abspath(sys.argv[0])
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{exe_path}"')
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception:
            pass

    def get_only_foreground(self):
        return self.data.get("only_foreground", True)

    def set_only_foreground(self, enabled):
        self.data["only_foreground"] = bool(enabled); self.save_config()

    def get_profile_names(self):
        return list(self.data["profiles"].keys())

    def get_active_profile_name(self):
        return self.data.get("active_profile", "")

    def set_active_profile(self, name):
        if name in self.data["profiles"]:
            self.data["active_profile"] = name
            self.save_config()

    def get_profile_rules(self, profile_name):
        return self.data["profiles"].get(profile_name, [])

    def create_profile(self, name):
        if name in self.data["profiles"]: return False, "配置已存在"
        self.data["profiles"][name] = []
        self.save_config()
        return True, "创建成功"

    def rename_profile(self, old_name, new_name):
        rules = self.data["profiles"].pop(old_name)
        self.data["profiles"][new_name] = rules
        self.save_config()
        return True, "重命名成功"

    def delete_profile(self, name):
        del self.data["profiles"][name]
        self.save_config()
        return True, "删除成功"

    def save_profile_rules(self, profile_name, rules):
        self.data["profiles"][profile_name] = rules
        self.save_config()

    def update_rule_msi_profile(self, profile_name, process_name, msi_profile_name):
        for rule in self.data["profiles"].get(profile_name, []):
            if rule.get("process", "").lower() == process_name.lower():
                rule["msi_profile"] = msi_profile_name
                self.save_config()
                return True
        return False
