from plugins.base_plugin import BasePlugin


class SettingsPlugin(BasePlugin):
    plugin_id = "settings"
    plugin_name = "全局设置"
    slot = "modal"
    order = 60

    def get_api_methods(self):
        return {
            "get_settings": self.get_settings,
            "save_settings": self.save_settings
        }

    def get_settings(self):
        cfg = self.context.get("config_mgr")
        if not cfg:
            return {"settings": {}, "profiles": []}
        return {
            "settings": cfg.get_settings(),
            "profiles": cfg.get_profile_names()
        }

    def save_settings(self, settings):
        cfg = self.context.get("config_mgr")
        if cfg:
            cfg.save_settings(settings)
        hotkey = settings.get("hotkey", "F12")
        hotkey_mgr = self.context.get("hotkey_mgr")
        if hotkey_mgr:
            hotkey_mgr.set_hotkey(hotkey)
            hotkey_mgr.start()
        if self.context.get("log"):
            self.context["log"]("系统配置已更新")
        return True
