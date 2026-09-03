import os
import time
try:
    import tkinter as tk
    from tkinter import filedialog
    HAS_TK = True
except ImportError:
    tk = None
    filedialog = None
    HAS_TK = False
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
from core.gpu_service import GPUService, is_admin, elevate_privileges
from core.power_service import PowerPlanService
from core.app_launcher import AppLauncher
from core.app_scanner import AppScanner
from core.icon_helper import IconHelper


class SoftwareManagerAPI:
    """提供给前端 JS 的统一网关接口"""

    def __init__(self, data_mgr, monitor_core, plugin_mgr):
        self._data_mgr = data_mgr
        self._monitor_core = monitor_core
        self._plugin_mgr = plugin_mgr
        self._logs = []

    def log(self, msg):
        if not self._data_mgr.get_settings().get("enable_logging", True):
            return
        t = time.strftime("%H:%M:%S")
        entry = f"[{t}] {msg}"
        self._logs.append(entry)
        if len(self._logs) > 300:
            self._logs.pop(0)

    def get_logs(self):
        if not self._data_mgr.get_settings().get("enable_logging", True):
            return ["(日志记录已在设置中关闭)"]
        return self._logs

    def clear_logs(self):
        self._logs.clear()
        return True

    def get_monitor_status(self):
        """实时返回监控核心与 GPU 硬件检测状态"""
        return self._monitor_core.get_monitor_status()

    def get_queue_apps(self):
        """排队器专用接口：返回当前按优先级排定的所有应用列表，并附带正在运行的状态"""
        ordered_apps = self._data_mgr.get_queue_order_apps()
        running_names = set()
        if HAS_PSUTIL:
            try:
                for p in psutil.process_iter(['name']):
                    try:
                        name = p.info['name']
                        if name:
                            running_names.add(name.strip().lower())
                    except Exception:
                        pass
            except Exception:
                pass

        results = []
        for a in ordered_apps:
            item = dict(a)
            if not item.get("custom_icon"):
                item["icon"] = IconHelper.get_icon_base64(item.get("exe_path") or item.get("exe_name"))
            exe = (item.get("exe_name") or "").strip().lower()
            item["is_running"] = (exe in running_names) if exe else False
            item["effective_tuning"] = self._data_mgr.get_effective_app_tuning(item)
            results.append(item)
        return results

    def save_queue_order(self, order_app_ids):
        self._data_mgr.save_queue_order(order_app_ids)
        self.log(f"[排队器] 已保存新优先级顺序 ({len(order_app_ids)} 项)")
        self._monitor_core.reapply_current_strategy()
        return {"success": True}

    def search_app_online(self, app_name):
        return self._plugin_mgr.dispatch("search_app_online", app_name)

    def capture_foreground_app(self, delay_seconds=0):
        return self._plugin_mgr.dispatch("capture_foreground_app", delay_seconds)

    def get_running_windows_processes(self):
        return self._plugin_mgr.dispatch("get_running_windows_processes")

    def validate_proxy_format(self, proxy_str):
        return self._plugin_mgr.dispatch("validate_proxy", proxy_str)

    def get_overview_data(self):
        apps = self._data_mgr.get_apps()
        total_count = len(apps)
        total_launches = sum(a.get("launch_count", 0) for a in apps)
        unused_count = sum(1 for a in apps if self._data_mgr.is_long_time_unused(a))

        sorted_recent = sorted(apps, key=lambda x: x.get("last_run_timestamp", 0), reverse=True)
        recent_app = sorted_recent[0] if sorted_recent else None
        if recent_app and not recent_app.get("custom_icon"):
            recent_app["icon"] = IconHelper.get_icon_base64(recent_app.get("exe_path") or recent_app.get("exe_name"))

        for a in sorted_recent:
            if not a.get("custom_icon"):
                a["icon"] = IconHelper.get_icon_base64(a.get("exe_path") or a.get("exe_name"))

        unused_apps = [a for a in sorted_recent if self._data_mgr.is_long_time_unused(a)]

        monitor_status = self._monitor_core.get_monitor_status()

        return {
            "total_count": total_count,
            "total_launches": total_launches,
            "unused_count": unused_count,
            "recent_app": recent_app,
            "recent_list": sorted_recent[:8],
            "unused_list": unused_apps[:8],
            "is_admin": is_admin(),
            "monitoring": self._monitor_core.monitoring,
            "monitor_status": monitor_status
        }

    def get_apps(self, category="全部", query="", sort_by="last_run", sort_order="desc", gpu_filter="全部", unused_only=False):
        apps = self._data_mgr.get_apps(category, query, sort_by, sort_order, gpu_filter, unused_only)
        for a in apps:
            if not a.get("custom_icon"):
                a["icon"] = IconHelper.get_icon_base64(a.get("exe_path") or a.get("exe_name"))
            a["effective_tuning"] = self._data_mgr.get_effective_app_tuning(a)
        return apps

    def get_app_detail(self, app_id):
        app = self._data_mgr.get_app_by_id(app_id)
        if app:
            if not app.get("custom_icon"):
                app["icon"] = IconHelper.get_icon_base64(app.get("exe_path") or app.get("exe_name"))
            app["is_unused"] = self._data_mgr.is_long_time_unused(app)
            app["effective_tuning"] = self._data_mgr.get_effective_app_tuning(app)
            app["group_config"] = self._data_mgr.get_group_config(app.get("category", ""))
        return app

    def save_app(self, app_data):
        res = self._data_mgr.save_app(app_data)
        AppLauncher.set_app_autostart(res.get("name"), res.get("exe_path"), res.get("auto_start", False))
        self.log(f"[配置保存] 已更新软件配置: [{res.get('name')}]")
        self._monitor_core.reapply_current_strategy()
        return {"success": True, "app": res}

    def rename_app(self, app_id, new_name):
        success, msg = self._data_mgr.rename_app(app_id, new_name)
        if success:
            self.log(f"已将软件重命名为: [{new_name}]")
        return {"success": success, "msg": msg}

    def delete_app(self, app_id):
        app = self._data_mgr.get_app_by_id(app_id)
        if app:
            AppLauncher.set_app_autostart(app.get("name"), app.get("exe_path"), False)
        self._data_mgr.delete_app(app_id)
        self.log(f"已删除软件: [{app_id}]")
        self._monitor_core.reapply_current_strategy()
        return {"success": True}

    def batch_delete_apps(self, app_ids):
        self._data_mgr.batch_delete(app_ids)
        self._monitor_core.reapply_current_strategy()
        return {"success": True}

    def batch_set_category(self, app_ids, category):
        self._data_mgr.batch_set_category(app_ids, category)
        self._monitor_core.reapply_current_strategy()
        return {"success": True}

    def batch_add_apps(self, app_list):
        added = self._data_mgr.batch_add_apps(app_list)
        self.log(f"批量导入了 {added} 个软件")
        self._monitor_core.reapply_current_strategy()
        return {"success": True, "count": added}

    def add_app_to_category(self, app_id, category_name, follow_policy=True):
        """将应用加入指定分组，并设置是否跟随此组策略"""
        success, msg = self._data_mgr.add_app_to_category(app_id, category_name, follow_policy)
        if success:
            app = self._data_mgr.get_app_by_id(app_id)
            app_name = app.get("name") if app else app_id
            self.log(f"[分组管理] 应用 [{app_name}] -> {msg}")
            self._monitor_core.reapply_current_strategy()
        return {"success": success, "msg": msg}

    def remove_app_from_category(self, app_id, category_name):
        """将应用从指定分组移出"""
        success, msg = self._data_mgr.remove_app_from_category(app_id, category_name)
        if success:
            app = self._data_mgr.get_app_by_id(app_id)
            app_name = app.get("name") if app else app_id
            self.log(f"[分组管理] 应用 [{app_name}] -> {msg}")
            self._monitor_core.reapply_current_strategy()
        return {"success": success, "msg": msg}

    def set_app_follow_group(self, app_id, group_name):
        """更新应用策略跟随目标分组或切换至独立定制"""
        success, msg = self._data_mgr.set_app_follow_group(app_id, group_name)
        if success:
            app = self._data_mgr.get_app_by_id(app_id)
            app_name = app.get("name") if app else app_id
            self.log(f"[策略调整] 应用 [{app_name}] -> {msg}")
            self._monitor_core.reapply_current_strategy()
        return {"success": success, "msg": msg}

    def get_group_config(self, category_name):
        return self._data_mgr.get_group_config(category_name)

    def save_group_config(self, category_name, config_data):
        self._data_mgr.save_group_config(category_name, config_data)
        self.log(f"[分组配置] 已更新分组 [{category_name}] 的统一策略")
        self._monitor_core.reapply_current_strategy()
        return {"success": True}

    def sync_group_config_to_apps(self, category_name):
        count = self._data_mgr.apply_group_config_to_apps(category_name)
        self.log(f"已将分组 [{category_name}] 配置同步至组内 {count} 个软件")
        self._monitor_core.reapply_current_strategy()
        return {"success": True, "count": count}

    def get_categories(self):
        return self._data_mgr.get_categories()

    def add_category(self, name):
        return self._data_mgr.add_category(name)

    def rename_category(self, old_name, new_name):
        success, msg = self._data_mgr.rename_category(old_name, new_name)
        if success:
            self.log(f"已将分组 [{old_name}] 重命名为: [{new_name}]")
        return {"success": success, "msg": msg}

    def delete_category(self, name):
        return self._data_mgr.delete_category(name)

    def get_settings(self):
        return self._data_mgr.get_settings()

    def save_settings(self, settings):
        self._data_mgr.save_settings(settings)
        self.log("[偏好设置] 系统偏好已更新")
        self._monitor_core.reapply_current_strategy()
        return True

    def launch_app(self, app_id):
        app = self._data_mgr.get_app_by_id(app_id)
        if not app:
            return {"success": False, "msg": "软件不存在"}
        path = app.get("exe_path") or app.get("exe_name")
        proxy = app.get("proxy_url", "").strip() or self._data_mgr.get_settings().get("global_proxy", "").strip()

        auto_msi = self._data_mgr.get_settings().get("auto_launch_msi", True)
        if auto_msi and self._monitor_core.msi_service.is_installed() and not self._monitor_core.msi_service.is_running():
            self._monitor_core.msi_service.launch_afterburner()

        success, msg = AppLauncher.launch_app(path, app_id=app_id, proxy_url=proxy)
        if success:
            self._data_mgr.record_launch(app_id)
            self.log(f"已启动软件: {app.get('name')}")
        return {"success": success, "msg": msg}

    def terminate_app(self, app_id):
        app = self._data_mgr.get_app_by_id(app_id)
        if not app:
            return {"success": False, "msg": "软件不存在"}
        exe_name = app.get("exe_name") or os.path.basename(app.get("exe_path", ""))
        success, msg = AppLauncher.terminate_app(exe_name)
        self.log(msg)
        return {"success": success, "msg": msg}

    def open_msi_vf_curve(self):
        msi = self._monitor_core.msi_service
        if not msi or not msi.is_installed():
            return {"success": False, "msg": "未检测到微星小飞机安装"}
        success, msg = msi.open_curve_editor()
        self.log(msg)
        return {"success": success, "msg": msg}

    def open_app_directory(self, app_id):
        app = self._data_mgr.get_app_by_id(app_id)
        if app and app.get("exe_path") and os.path.exists(app["exe_path"]):
            folder = os.path.dirname(app["exe_path"])
            os.startfile(folder)
            return {"success": True}
        return {"success": False, "msg": "路径不存在"}

    def scan_installed_apps(self):
        apps = AppScanner.get_installed_apps()
        for a in apps:
            a["icon"] = IconHelper.get_icon_base64(a.get("exe_path") or a.get("exe_name"))
        return apps

    def get_power_plans(self):
        return PowerPlanService.get_power_plans()

    def get_msi_profiles(self):
        msi = self._monitor_core.msi_service
        if msi and msi.is_installed():
            return msi.get_profile_names()
        return []

    def browse_executable_files(self):
        if not HAS_TK:
            return {"success": False, "error": "未检测到图形界面文件选择模块"}
        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            file_paths = filedialog.askopenfilenames(
                title="选择可执行程序 (.exe) - 可按住 Ctrl 多选",
                filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")]
            )
            root.destroy()
            if file_paths:
                results = []
                for p in file_paths:
                    norm_path = os.path.normpath(p)
                    exe_name = os.path.basename(norm_path)
                    app_name = os.path.splitext(exe_name)[0]
                    icon_b64 = IconHelper.get_icon_base64(norm_path)
                    results.append({
                        "exe_path": norm_path,
                        "exe_name": exe_name,
                        "name": app_name,
                        "icon": icon_b64
                    })
                return {"success": True, "files": results}
        except Exception as e:
            return {"success": False, "error": str(e)}
        return {"success": False, "cancelled": True}

    def browse_wallpaper_file(self):
        """选择本地图片作为自定义壁纸"""
        if not HAS_TK:
            return {"success": False, "error": "未检测到图形界面文件选择模块"}
        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            file_path = filedialog.askopenfilename(
                title="选择背景壁纸图片",
                filetypes=[
                    ("图片文件", "*.jpg;*.jpeg;*.png;*.webp;*.bmp"),
                    ("所有文件", "*.*")
                ]
            )
            root.destroy()
            if file_path and os.path.exists(file_path):
                import base64
                with open(file_path, "rb") as img_f:
                    b64_data = base64.b64encode(img_f.read()).decode("utf-8")
                ext = os.path.splitext(file_path)[1].lower().strip(".")
                mime = f"image/{ext}" if ext != "jpg" else "image/jpeg"
                data_url = f"data:{mime};base64,{b64_data}"
                
                # 自动保存到 settings
                s = self._data_mgr.get_settings()
                s["custom_wallpaper"] = data_url
                self._data_mgr.save_settings(s)
                self.log(f"[偏好设置] 已更新自定义背景壁纸: {os.path.basename(file_path)}")
                return {"success": True, "wallpaper": data_url, "path": file_path}
        except Exception as e:
            return {"success": False, "error": str(e)}
        return {"success": False, "cancelled": True}

    def clear_wallpaper(self):
        """清除自定义壁纸，恢复纯色背景"""
        s = self._data_mgr.get_settings()
        s["custom_wallpaper"] = ""
        self._data_mgr.save_settings(s)
        self.log("[偏好设置] 已清除自定义壁纸，恢复系统默认背景")
        return {"success": True}

    def save_sidebar_state(self, collapsed):
        """保存边栏展开/收起状态"""
        s = self._data_mgr.get_settings()
        s["sidebar_collapsed"] = bool(collapsed)
        self._data_mgr.save_settings(s)
        return {"success": True, "collapsed": bool(collapsed)}

    def reset_appearance_settings(self):
        """一键重置外观样式配置"""
        s = self._data_mgr.get_settings()
        s["custom_wallpaper"] = ""
        s["custom_wallpaper_fit"] = "cover"
        s["custom_text_color"] = ""
        s["custom_primary_color"] = ""
        s["ui_opacity"] = 0.90
        s["ui_blur"] = 16
        self._data_mgr.save_settings(s)
        self.log("[偏好设置] 外观个性化样式已恢复默认值")
        return {"success": True, "settings": s}

    def browse_custom_icon_file(self, app_id):
        if not HAS_TK:
            return {"success": False, "error": "未检测到图形界面文件选择模块"}
        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            file_path = filedialog.askopenfilename(
                title="选择图标文件或图片",
                filetypes=[
                    ("图标与图片文件", "*.ico;*.png;*.jpg;*.jpeg;*.bmp;*.exe;*.webp"),
                    ("所有文件", "*.*")
                ]
            )
            root.destroy()
            if file_path and os.path.exists(file_path):
                icon_b64 = IconHelper.convert_image_file_to_base64(file_path)
                self._data_mgr.update_app_icon(app_id, icon_b64)
                self.log(f"已更新应用 [{app_id}] 的自定义图标")
                return {"success": True, "icon": icon_b64}
        except Exception as e:
            return {"success": False, "error": str(e)}
        return {"success": False, "cancelled": True}

    def export_backup(self):
        if not HAS_TK:
            return {"success": False, "error": "未检测到图形界面文件选择模块"}
        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            save_path = filedialog.asksaveasfilename(
                title="保存备份文件",
                defaultextension=".json",
                initialfile="NanakoManager_Backup.json",
                filetypes=[("JSON 备份文件", "*.json")]
            )
            root.destroy()
            if save_path:
                json_content = self._data_mgr.export_backup_json()
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(json_content)
                self.log(f"已成功导出备份文件至: {save_path}")
                return {"success": True, "path": save_path}
        except Exception as e:
            return {"success": False, "error": str(e)}
        return {"success": False, "cancelled": True}

    def import_backup(self):
        if not HAS_TK:
            return {"success": False, "error": "未检测到图形界面文件选择模块"}
        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            file_path = filedialog.askopenfilename(
                title="选择要恢复的 JSON 备份文件",
                filetypes=[("JSON 备份文件", "*.json"), ("所有文件", "*.*")]
            )
            root.destroy()
            if file_path and os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                success, msg = self._data_mgr.import_backup_json(content)
                if success:
                    self.log(f"备份恢复成功: {msg}")
                return {"success": success, "msg": msg}
        except Exception as e:
            return {"success": False, "error": str(e)}
        return {"success": False, "cancelled": True}

    def elevate_admin(self):
        success, msg = elevate_privileges()
        return {"success": success, "msg": msg}

    def toggle_monitor(self):
        if self._monitor_core.monitoring:
            self._monitor_core.stop()
        else:
            self._monitor_core.start()
        return self._monitor_core.get_monitor_status()
