from plugins.base_plugin import BasePlugin


class MSIPlugin(BasePlugin):
    plugin_id = "msi"
    plugin_name = "微星小飞机控制器"
    slot = "main"
    order = 35

    def get_api_methods(self):
        return {
            "get_profiles": self.get_profiles,
            "open_vf_curve": self.open_vf_curve,
            "apply_profile": self.apply_profile
        }

    def get_profiles(self):
        msi = self.context.get("msi_service")
        if not msi or not msi.is_installed():
            return []
        return msi.get_profile_names()

    def open_vf_curve(self):
        msi = self.context.get("msi_service")
        if msi:
            success, msg = msi.open_curve_editor()
            self.context["log"](msg)
            return {"success": success, "msg": msg}
        return {"success": False, "msg": "未安装微星小飞机"}

    def apply_profile(self, profile_name):
        msi = self.context.get("msi_service")
        if msi:
            p = msi.get_profile_by_name(profile_name)
            if p:
                success, msg = msi.apply_profile(p["id"])
                self.context["log"](msg)
                return {"success": success, "msg": msg}
        return {"success": False, "msg": "配置无效"}
