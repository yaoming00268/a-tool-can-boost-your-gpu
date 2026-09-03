import json
import os
import time
import datetime
import re


def sanitize_app_name(text):
    if not text:
        return ""
    text = str(text).replace('\ufffd', '')
    text = re.sub(r'[\x00-\x1f\x7f-\x9f\u200b-\u200f\ufeff]', '', text)
    text = text.strip(' \t\r\n\u3000\u00a0')
    text = re.sub(r'[ \t\u3000\u00a0]+', ' ', text)
    return text


class SoftwareDataManager:
    """本地软件数据库、排队器顺序、调度模式、分类分组、GPU/电源定制与网络代理管理器"""

    DB_FILE = "software_library.json"

    def __init__(self, db_file=DB_FILE):
        self.db_file = db_file
        self.data = self._load_data()

    def _load_data(self):
        default_data = {
            "settings": {
                "auto_start": False,
                "auto_start_monitor": True,     # 打开软件时自动启动监控
                "auto_launch_msi": True,
                "hotkey": "F12",
                "default_power_plan": "",
                "theme": "light",
                "policy_mode": "individual",
                "schedule_mode": "focus",       # focus (焦点模式) | queue (排队器模式)
                "global_mode": True,            # 全局模式开关：True 时识别系统所有打开进程，False 时仅识别由本软件启动的进程
                "enable_logging": True,         # 是否打开日志记录
                "enable_gpu_buffer": True,      # 是否启用显卡调频缓冲器 (阶梯平滑过渡)
                "gpu_ramp_step": 150,
                "gpu_ramp_delay": 0.035,        # 调频平滑单步跨度 (MHz)
                "enable_web_search": True,
                "search_engine": "bing",
                "custom_search_url": "https://search.bilibili.com/all?keyword={keyword}&from_source=webhistory_search",
                "global_proxy": "",
                "queue_order": [],               # 排队器模式下的应用 ID 排序列表
                "custom_wallpaper": "",         # 自定义背景壁纸 (Base64 或本地文件路径)
                "custom_wallpaper_fit": "cover",# 壁纸填充方式: cover | contain
                "custom_text_color": "",        # 自定义主文本颜色 (如 #1E293B)
                "custom_primary_color": "",     # 自定义主题强调主色 (如 #2563EB)
                "ui_opacity": 0.90,             # UI组件透明度 (0.2 ~ 1.0)
                "ui_blur": 16,                  # 毛玻璃模糊度 (px, 0 ~ 30)
                "sidebar_collapsed": False      # 边栏是否收起
            },
            "categories": ["全部", "常用工具", "开发与生产力", "渲染与设计", "日常软件"],
            "group_configs": {},
            "apps": []
        }
        if not os.path.exists(self.db_file):
            return default_data
        try:
            with open(self.db_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "apps" not in data: data["apps"] = []
                if "categories" not in data: data["categories"] = default_data["categories"]
                if "group_configs" not in data: data["group_configs"] = {}
                if "settings" not in data: data["settings"] = default_data["settings"]

                s = data["settings"]
                s.setdefault("auto_start_monitor", True)
                s.setdefault("policy_mode", "individual")
                s.setdefault("schedule_mode", "focus")
                s.setdefault("global_mode", True)
                s.setdefault("enable_logging", True)
                s.setdefault("enable_gpu_buffer", True)
                s.setdefault("gpu_ramp_step", 150)
                s.setdefault("gpu_ramp_delay", 0.035)
                s.setdefault("queue_order", [])
                s.setdefault("enable_web_search", True)
                s.setdefault("search_engine", "bing")
                s.setdefault("custom_search_url", "https://search.bilibili.com/all?keyword={keyword}&from_source=webhistory_search")
                s.setdefault("global_proxy", "")
                s.setdefault("custom_wallpaper", "")
                s.setdefault("custom_wallpaper_fit", "cover")
                s.setdefault("custom_text_color", "")
                s.setdefault("custom_primary_color", "")
                s.setdefault("ui_opacity", 0.90)
                s.setdefault("ui_blur", 16)
                s.setdefault("sidebar_collapsed", False)

# 自动对库中历史数据进行名称清洗与多分组结构兼容升级
                for a in data.get("apps", []):
                    if "name" in a:
                        a["name"] = sanitize_app_name(a["name"])
                    if "exe_name" in a:
                        a["exe_name"] = sanitize_app_name(a["exe_name"])
                    # 多分组结构支持
                    cat = a.get("category", "常用工具")
                    cats = a.get("categories")
                    if not cats or not isinstance(cats, list):
                        cats = [cat] if cat else ["常用工具"]
                    if cat and cat not in cats:
                        cats.append(cat)
                    a["categories"] = cats
                    if not a.get("follow_group"):
                        a["follow_group"] = cat if not a.get("override_group_config", False) else "独立定制"
                return data
        except Exception:
            return default_data

    def save(self):
        try:
            with open(self.db_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    def is_long_time_unused(self, app):
        now = time.time()
        thirty_days = 30 * 86400
        last_ts = app.get("last_run_timestamp", 0)

        if last_ts == 0 and app.get("last_run_time") and app.get("last_run_time") != "从未运行":
            try:
                dt = datetime.datetime.strptime(app.get("last_run_time"), "%Y-%m-%d %H:%M")
                last_ts = int(dt.timestamp())
                app["last_run_timestamp"] = last_ts
            except Exception:
                pass

        if last_ts > 0:
            return (now - last_ts) > thirty_days

        added_ts = app.get("added_timestamp", 0)
        if added_ts > 0 and (now - added_ts) > thirty_days:
            return True
        return False

    def get_group_config(self, category_name):
        default_cfg = {
            "gpu_mode": "不修改",
            "gpu_freq": 2200,
            "gpu_min_freq": 200,
            "gpu_max_freq": 3500,
            "power_plan_guid": "默认",
            "msi_profile": "默认配置"
        }
        return self.data.get("group_configs", {}).get(category_name, default_cfg)

    def save_group_config(self, category_name, config_data):
        if "group_configs" not in self.data:
            self.data["group_configs"] = {}
        self.data["group_configs"][category_name] = config_data
        self.save()
        return True

    def apply_group_config_to_apps(self, category_name):
        g_cfg = self.get_group_config(category_name)
        count = 0
        for app in self.data.get("apps", []):
            if app.get("category") == category_name:
                app["gpu_mode"] = g_cfg.get("gpu_mode", "不修改")
                app["gpu_freq"] = g_cfg.get("gpu_freq", 2200)
                app["gpu_min_freq"] = g_cfg.get("gpu_min_freq", 200)
                app["gpu_max_freq"] = g_cfg.get("gpu_max_freq", 3500)
                app["power_plan_guid"] = g_cfg.get("power_plan_guid", "默认")
                app["msi_profile"] = g_cfg.get("msi_profile", "默认配置")
                app["override_group_config"] = False
                count += 1
        self.save()
        return count

    def get_effective_app_tuning(self, app):
        policy_mode = self.data.get("settings", {}).get("policy_mode", "individual")
        follow_group = app.get("follow_group")
        is_override = app.get("override_group_config", False) or (follow_group == "独立定制")
        
        # 确定主跟随分组
        target_group = follow_group if (follow_group and follow_group != "独立定制") else (app.get("category") or "常用工具")
        group_cfg = self.get_group_config(target_group)

        # 若跟随指定分组 (未脱离独立定制，或系统处于分组继承模式)
        if not is_override and target_group:
            return {
                "source": "group",
                "category": target_group,
                "follow_group": target_group,
                "gpu_mode": group_cfg.get("gpu_mode", "不修改"),
                "gpu_freq": group_cfg.get("gpu_freq", 2200),
                "gpu_min_freq": group_cfg.get("gpu_min_freq", 200),
                "gpu_max_freq": group_cfg.get("gpu_max_freq", 3500),
                "power_plan_guid": group_cfg.get("power_plan_guid", "默认"),
                "msi_profile": group_cfg.get("msi_profile", "默认配置")
            }
        else:
            return {
                "source": "individual",
                "category": target_group,
                "follow_group": "独立定制",
                "gpu_mode": app.get("gpu_mode", "不修改"),
                "gpu_freq": app.get("gpu_freq", 2200),
                "gpu_min_freq": app.get("gpu_min_freq", 200),
                "gpu_max_freq": app.get("gpu_max_freq", 3500),
                "power_plan_guid": app.get("power_plan_guid", "默认"),
                "msi_profile": app.get("msi_profile", "默认配置")
            }

    def get_apps(self, category="全部", search_query="", sort_by="last_run", sort_order="desc", gpu_filter="全部", unused_only=False):
        apps = self.data.get("apps", [])
        filtered = []
        q = (search_query or "").strip().lower()

        for app in apps:
            if category != "全部":
                app_cats = app.get("categories", [])
                if not app_cats:
                    app_cats = [app.get("category", "常用工具")]
                if category not in app_cats and app.get("category") != category:
                    continue

            effective_tuning = self.get_effective_app_tuning(app)
            if gpu_filter != "全部" and effective_tuning["gpu_mode"] != gpu_filter:
                continue
            if unused_only and not self.is_long_time_unused(app):
                continue
            if q:
                name_match = q in app.get("name", "").lower()
                exe_match = q in app.get("exe_name", "").lower()
                path_match = q in app.get("exe_path", "").lower()
                if not (name_match or exe_match or path_match):
                    continue
            filtered.append(app)

        reverse = (sort_order == "desc")
        if sort_by == "name":
            filtered.sort(key=lambda x: x.get("name", "").lower(), reverse=reverse)
        elif sort_by == "launch_count":
            filtered.sort(key=lambda x: x.get("launch_count", 0), reverse=reverse)
        elif sort_by == "add_time":
            filtered.sort(key=lambda x: x.get("added_timestamp", 0), reverse=reverse)
        else:
            filtered.sort(key=lambda x: x.get("last_run_timestamp", 0), reverse=reverse)

        return filtered

    def get_app_by_id(self, app_id):
        for app in self.data.get("apps", []):
            if app.get("id") == app_id:
                return app
        return None

    def get_app_by_process(self, process_name, full_path=None, pid=None):
        if not process_name:
            return None
        from core.app_launcher import AppLauncher

        # 1. 若有 PID，优先从启动器精确映射中解析
        if pid:
            app_id = AppLauncher.get_app_id_by_pid(pid)
            if app_id:
                app = self.get_app_by_id(app_id)
                if app:
                    return app

        # 2. 若有完整路径，优先进行完整路径绝对匹配
        if full_path:
            norm_target_path = os.path.normpath(full_path).strip().lower()
            for app in self.data.get("apps", []):
                app_p = (app.get("exe_path") or "").strip().lower()
                if app_p and os.path.normpath(app_p) == norm_target_path:
                    return app

        p_clean = process_name.strip().lower()
        p_without_exe = p_clean[:-4] if p_clean.endswith(".exe") else p_clean
        p_with_exe = p_clean if p_clean.endswith(".exe") else (p_clean + ".exe")

        matched_candidates = []
        for app in self.data.get("apps", []):
            app_exe = (app.get("exe_name") or "").strip().lower()
            app_path = (app.get("exe_path") or "").strip().lower()
            app_base = os.path.basename(app_path) if app_path else ""

            candidates = {app_exe, app_base}
            if app_exe.endswith(".exe"):
                candidates.add(app_exe[:-4])
            else:
                candidates.add(app_exe + ".exe")
            if app_base.endswith(".exe"):
                candidates.add(app_base[:-4])
            else:
                candidates.add(app_base + ".exe")

            if p_clean in candidates or p_without_exe in candidates or p_with_exe in candidates:
                matched_candidates.append(app)

        if not matched_candidates:
            return None

        if len(matched_candidates) == 1:
            return matched_candidates[0]

        # 3. 若存在多个同名应用（如多个 osu!.exe），按智能优先级决策：
        # 优先级 a: 优先匹配最近通过管理器启动的应用
        last_id = AppLauncher.get_last_launched_app_id()
        if last_id:
            for a in matched_candidates:
                if a.get("id") == last_id:
                    return a

        # 优先级 b: 优先匹配已经配置了专属策略的应用（排除 '不修改' 的空配置应用）
        tuned_apps = [a for a in matched_candidates if a.get("gpu_mode", "不修改") != "不修改"]
        if tuned_apps:
            # 在已调优的应用中，取最近运行的
            tuned_apps.sort(key=lambda x: x.get("last_run_timestamp", 0), reverse=True)
            return tuned_apps[0]

        # 优先级 c: 兜底取最近运行的应用
        matched_candidates.sort(key=lambda x: x.get("last_run_timestamp", 0), reverse=True)
        return matched_candidates[0]
        p_clean = process_name.strip().lower()
        p_without_exe = p_clean[:-4] if p_clean.endswith(".exe") else p_clean
        p_with_exe = p_clean if p_clean.endswith(".exe") else (p_clean + ".exe")

        for app in self.data.get("apps", []):
            app_exe = (app.get("exe_name") or "").strip().lower()
            app_path = (app.get("exe_path") or "").strip().lower()
            app_base = os.path.basename(app_path) if app_path else ""

            candidates = {app_exe, app_base}
            if app_exe.endswith(".exe"):
                candidates.add(app_exe[:-4])
            else:
                candidates.add(app_exe + ".exe")
            if app_base.endswith(".exe"):
                candidates.add(app_base[:-4])
            else:
                candidates.add(app_base + ".exe")

            if p_clean in candidates or p_without_exe in candidates or p_with_exe in candidates:
                return app
        return None

    def save_app(self, app_data):
        apps = self.data.get("apps", [])
        app_data["name"] = sanitize_app_name(app_data.get("name", ""))
        app_data["exe_name"] = sanitize_app_name(app_data.get("exe_name", ""))
        app_id = app_data.get("id")
        if not app_id:
            app_id = f"app_{int(time.time()*1000)}"
            app_data["id"] = app_id
            app_data.setdefault("added_timestamp", int(time.time()))
            app_data.setdefault("launch_count", 0)
            app_data.setdefault("last_run_time", "从未运行")
            app_data.setdefault("last_run_timestamp", 0)
            cat_val = app_data.get("category", "常用工具")
            app_data.setdefault("category", cat_val)
            app_data.setdefault("categories", [cat_val] if cat_val else ["常用工具"])
            app_data.setdefault("follow_group", cat_val)
            app_data.setdefault("proxy_url", "")
            app_data.setdefault("override_group_config", False)
            apps.append(app_data)
            q_order = self.data.get("settings", {}).get("queue_order", [])
            if app_id not in q_order:
                q_order.append(app_id)
                self.data["settings"]["queue_order"] = q_order
        else:
            found = False
            for idx, existing in enumerate(apps):
                if existing.get("id") == app_id:
                    app_data["added_timestamp"] = existing.get("added_timestamp", int(time.time()))
                    app_data["launch_count"] = existing.get("launch_count", 0)
                    app_data["last_run_time"] = existing.get("last_run_time", "从未运行")
                    app_data["last_run_timestamp"] = existing.get("last_run_timestamp", 0)
                    apps[idx] = app_data
                    found = True
                    break
            if not found:
                apps.append(app_data)
                q_order = self.data.get("settings", {}).get("queue_order", [])
                if app_id not in q_order:
                    q_order.append(app_id)
                    self.data["settings"]["queue_order"] = q_order
        self.data["apps"] = apps
        self.save()
        return app_data

    def rename_app(self, app_id, new_name):
        app = self.get_app_by_id(app_id)
        if app and new_name and new_name.strip():
            app["name"] = new_name.strip()
            self.save()
            return True, "重命名成功"
        return False, "应用不存在或名称无效"

    def batch_add_apps(self, app_list):
        apps = self.data.get("apps", [])
        existing_paths = {a.get("exe_path", "").lower() for a in apps}
        added_count = 0
        now = int(time.time())
        q_order = self.data.get("settings", {}).get("queue_order", [])

        for item in app_list:
            path = item.get("exe_path", "")
            if path and path.lower() in existing_paths:
                continue
            item_id = f"app_{int(time.time()*1000)}_{added_count}"
            item["id"] = item_id
            item.setdefault("added_timestamp", now)
            item.setdefault("launch_count", 0)
            item.setdefault("last_run_time", "从未运行")
            item.setdefault("last_run_timestamp", 0)
            item.setdefault("category", "常用工具")
            item.setdefault("proxy_url", "")
            item.setdefault("override_group_config", False)
            apps.append(item)
            existing_paths.add(path.lower())
            if item_id not in q_order:
                q_order.append(item_id)
            added_count += 1

        self.data["settings"]["queue_order"] = q_order
        self.data["apps"] = apps
        self.save()
        return added_count

    def update_app_icon(self, app_id, icon_base64):
        app = self.get_app_by_id(app_id)
        if app:
            app["icon"] = icon_base64
            app["custom_icon"] = True
            self.save()
            return True
        return False

    def delete_app(self, app_id):
        self.data["apps"] = [a for a in self.data.get("apps", []) if a.get("id") != app_id]
        q_order = self.data.get("settings", {}).get("queue_order", [])
        if app_id in q_order:
            q_order.remove(app_id)
            self.data["settings"]["queue_order"] = q_order
        self.save()
        return True

    def batch_delete(self, app_ids):
        id_set = set(app_ids)
        self.data["apps"] = [a for a in self.data.get("apps", []) if a.get("id") not in id_set]
        q_order = self.data.get("settings", {}).get("queue_order", [])
        self.data["settings"]["queue_order"] = [aid for aid in q_order if aid not in id_set]
        self.save()
        return True

    def batch_set_category(self, app_ids, category):
        id_set = set(app_ids)
        for app in self.data.get("apps", []):
            if app.get("id") in id_set:
                app["category"] = category
        self.save()
        return True

    def record_launch(self, app_id):
        app = self.get_app_by_id(app_id)
        if app:
            now_ts = int(time.time())
            app["launch_count"] = app.get("launch_count", 0) + 1
            app["last_run_time"] = time.strftime("%Y-%m-%d %H:%M")
            app["last_run_timestamp"] = now_ts
            self.save()


    def add_app_to_category(self, app_id, category_name, follow_policy=True):
        """将应用加入指定分组，并可选择是否跟随该分组策略"""
        app = self.get_app_by_id(app_id)
        if not app:
            return False, "应用不存在"
        cats = app.get("categories", [])
        if category_name not in cats:
            cats.append(category_name)
        app["categories"] = cats
        if follow_policy:
            app["follow_group"] = category_name
            app["category"] = category_name
            app["override_group_config"] = False
        self.save()
        return True, f"已将应用加入分组【{category_name}】" + (" 并跟随其调控策略" if follow_policy else "")

    def remove_app_from_category(self, app_id, category_name):
        """将应用从指定分组移出"""
        app = self.get_app_by_id(app_id)
        if not app:
            return False, "应用不存在"
        cats = app.get("categories", [])
        if category_name in cats:
            cats.remove(category_name)
        if not cats:
            cats = ["常用工具"]
        app["categories"] = cats
        if app.get("follow_group") == category_name or app.get("category") == category_name:
            app["follow_group"] = cats[0]
            app["category"] = cats[0]
        self.save()
        return True, f"已从分组【{category_name}】中移出"

    def set_app_follow_group(self, app_id, group_name):
        """设置应用当前跟随的策略分组或独立定制"""
        app = self.get_app_by_id(app_id)
        if not app:
            return False, "应用不存在"
        if group_name == "独立定制":
            app["override_group_config"] = True
            app["follow_group"] = "独立定制"
        else:
            app["override_group_config"] = False
            app["follow_group"] = group_name
            app["category"] = group_name
            cats = app.get("categories", [])
            if group_name not in cats and group_name != "全部":
                cats.append(group_name)
            app["categories"] = cats
        self.save()
        return True, f"已将策略选择变更为: {group_name}"

    def get_categories(self):
        return self.data.get("categories", [])

    def add_category(self, name):
        cats = self.data.get("categories", [])
        if name and name not in cats:
            cats.append(name)
            self.data["categories"] = cats
            self.save()
            return True
        return False

    def rename_category(self, old_name, new_name):
        if not new_name or not new_name.strip() or old_name == "全部":
            return False, "无效的分组名称"
        new_name = new_name.strip()
        cats = self.data.get("categories", [])
        if old_name in cats:
            if new_name in cats and new_name != old_name:
                return False, "已存在同名分组"
            idx = cats.index(old_name)
            cats[idx] = new_name
            self.data["categories"] = cats

            if "group_configs" in self.data and old_name in self.data["group_configs"]:
                self.data["group_configs"][new_name] = self.data["group_configs"].pop(old_name)

            for a in self.data.get("apps", []):
                if a.get("category") == old_name:
                    a["category"] = new_name
            self.save()
            return True, "分组重命名成功"
        return False, "原分组不存在"

    def delete_category(self, name):
        if name in ["全部", "常用工具"]:
            return False
        cats = self.data.get("categories", [])
        if name in cats:
            cats.remove(name)
            for a in self.data.get("apps", []):
                if a.get("category") == name:
                    a["category"] = "常用工具"
            self.data["categories"] = cats
            if name in self.data.get("group_configs", {}):
                del self.data["group_configs"][name]
            self.save()
            return True
        return False

    def get_settings(self):
        return self.data.get("settings", {})

    def save_settings(self, settings):
        self.data["settings"] = settings
        self.save()

    def get_queue_order_apps(self):
        apps = self.data.get("apps", [])
        app_map = {a["id"]: a for a in apps}
        q_order = self.data.get("settings", {}).get("queue_order", [])

        ordered_apps = []
        seen_ids = set()

        for aid in q_order:
            if aid in app_map:
                ordered_apps.append(app_map[aid])
                seen_ids.add(aid)

        for a in apps:
            if a["id"] not in seen_ids:
                ordered_apps.append(a)

        return ordered_apps

    def save_queue_order(self, order_app_ids):
        if "settings" not in self.data:
            self.data["settings"] = {}
        self.data["settings"]["queue_order"] = order_app_ids
        self.save()
        return True

    def export_backup_json(self):
        return json.dumps(self.data, ensure_ascii=False, indent=2)

    def import_backup_json(self, json_str):
        try:
            data = json.loads(json_str)
            if "apps" in data and "settings" in data:
                self.data = data
                self.save()
                return True, f"成功恢复 {len(data.get('apps', []))} 个软件及全部分组调优配置"
            return False, "备份文件格式不合法"
        except Exception as e:
            return False, f"解析备份数据失败: {str(e)}"
