try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
from plugins.base_plugin import BasePlugin
from core.app_scanner import AppScanner
from core.icon_helper import IconHelper


class ProcessToolsPlugin(BasePlugin):
    plugin_id = "tools"
    plugin_name = "进程工具与导入"
    slot = "modal"
    order = 50

    def get_api_methods(self):
        return {
            "get_running_processes": self.get_running_processes,
            "get_installed_apps": self.get_installed_apps,
            "import_selected_apps": self.import_selected_apps
        }

    def get_running_processes(self):
        procs = []
        seen = set()
        for p in psutil.process_iter(["pid", "name", "exe"]):
            try:
                name = p.info["name"]
                if name and name.lower().endswith(".exe") and name.lower() not in seen:
                    seen.add(name.lower())
                    procs.append({
                        "name": name,
                        "pid": p.info["pid"],
                        "icon": IconHelper.get_icon_base64(p.info["exe"] or name)
                    })
            except Exception:
                pass
        return sorted(procs, key=lambda x: x["name"].lower())

    def get_installed_apps(self):
        apps = AppScanner.get_installed_apps()
        for app in apps:
            app["icon"] = IconHelper.get_icon_base64(app.get("exe_path") or app.get("exe_name"))
        return apps

    def import_selected_apps(self, app_list, default_freq):
        cfg = self.context.get("config_mgr")
        if not cfg:
            return False
        active = cfg.get_active_profile_name()
        if not active:
            return False

        rules = cfg.get_profile_rules(active)
        for exe in app_list:
            if not any(r["process"].lower() == exe.lower() for r in rules):
                rules.append({
                    "process": exe,
                    "mode": "定频模式",
                    "frequency": default_freq,
                    "min_freq": 200,
                    "max_freq": 4000,
                    "msi_profile": None
                })
        cfg.save_profile_rules(active, rules)
        if self.context.get("log"):
            self.context["log"](f"成功导入 {len(app_list)} 个应用程序规则")
        return True
