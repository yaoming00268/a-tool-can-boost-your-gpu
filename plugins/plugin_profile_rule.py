from plugins.base_plugin import BasePlugin
from core.icon_helper import IconHelper
from core.app_launcher import AppLauncher


class ProfileRulePlugin(BasePlugin):
    plugin_id = "rules"
    plugin_name = "规则与配置管理"
    slot = "main"
    order = 20

    def get_api_methods(self):
        return {
            "get_profiles": self.get_profiles,
            "set_active_profile": self.set_active_profile,
            "create_profile": self.create_profile,
            "delete_profile": self.delete_profile,
            "get_rules": self.get_rules,
            "save_rule": self.save_rule,
            "delete_rule": self.delete_rule,
            "launch_rule_app": self.launch_rule_app
        }

    def get_profiles(self):
        cfg = self.context.get("config_mgr")
        if not cfg:
            return {"profiles": [], "active": ""}
        return {
            "profiles": cfg.get_profile_names(),
            "active": cfg.get_active_profile_name()
        }

    def set_active_profile(self, name):
        cfg = self.context.get("config_mgr")
        if cfg:
            cfg.set_active_profile(name)
        return self.get_rules()

    def create_profile(self, name):
        cfg = self.context.get("config_mgr")
        return cfg.create_profile(name) if cfg else (False, "未配置管理器")

    def delete_profile(self, name):
        cfg = self.context.get("config_mgr")
        return cfg.delete_profile(name) if cfg else (False, "未配置管理器")

    def get_rules(self):
        cfg = self.context.get("config_mgr")
        if not cfg:
            return []
        active = cfg.get_active_profile_name()
        rules = cfg.get_profile_rules(active)
        for r in rules:
            r["icon"] = IconHelper.get_icon_base64(r["process"])
        return rules

    def save_rule(self, rule_data):
        cfg = self.context.get("config_mgr")
        if not cfg:
            return False, "未配置管理器"
        active = cfg.get_active_profile_name()
        if not active:
            return False, "未选择配置方案"

        proc = rule_data.get("process", "").strip()
        if not proc.lower().endswith(".exe"):
            proc += ".exe"
        rule_data["process"] = proc

        rules = cfg.get_profile_rules(active)
        new_rules = [r for r in rules if r["process"].lower() != proc.lower()]
        new_rules.append(rule_data)
        cfg.save_profile_rules(active, new_rules)
        if self.context.get("log"):
            self.context["log"](f"已保存规则: {proc}")
        return True, "规则已保存"

    def delete_rule(self, proc_name):
        cfg = self.context.get("config_mgr")
        if not cfg:
            return False
        active = cfg.get_active_profile_name()
        rules = cfg.get_profile_rules(active)
        cfg.save_profile_rules(active, [r for r in rules if r["process"].lower() != proc_name.lower()])
        if self.context.get("log"):
            self.context["log"](f"已删除规则: {proc_name}")
        return True

    def launch_rule_app(self, proc_name):
        success, msg = AppLauncher.launch_app(proc_name)
        if self.context.get("log"):
            self.context["log"](msg)
        return {"success": success, "msg": msg}
