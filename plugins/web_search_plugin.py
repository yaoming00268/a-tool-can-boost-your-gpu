import urllib.parse
import webbrowser
import os
from plugins.base_plugin import BasePlugin


class WebSearchPlugin(BasePlugin):
    plugin_id = "web_search"
    plugin_name = "网页搜索与跳转插件"
    order = 10

    def get_api_methods(self):
        return {
            "search_app_online": self.search_app_online
        }

    def search_app_online(self, app_name):
        if not app_name or not app_name.strip():
            return {"success": False, "msg": "应用名为空"}

        data_mgr = self.context.get("data_mgr")
        if not data_mgr:
            return {"success": False, "msg": "数据管理器未就绪"}
        settings = data_mgr.get_settings()
        engine = settings.get("search_engine", "bing")
        custom_url = settings.get("custom_search_url", "").strip()
        encoded_kw = urllib.parse.quote(app_name.strip())

        preset_urls = {
            "bing": "https://www.bing.com/search?q={keyword}",
            "google": "https://www.google.com/search?q={keyword}",
            "baidu": "https://www.baidu.com/s?wd={keyword}",
            "bilibili": "https://search.bilibili.com/all?keyword={keyword}&from_source=webhistory_search",
            "github": "https://github.com/search?q={keyword}"
        }

        if engine == "custom" and custom_url:
            target_url = custom_url
            if "{keyword}" in target_url:
                target_url = target_url.replace("{keyword}", encoded_kw)
            elif "%s" in target_url:
                target_url = target_url.replace("%s", encoded_kw)
            elif "（跳转时填入）" in target_url:
                target_url = target_url.replace("（跳转时填入）", encoded_kw)
            else:
                target_url += encoded_kw
        else:
            tpl = preset_urls.get(engine, preset_urls["bing"])
            target_url = tpl.replace("{keyword}", encoded_kw)

        global_proxy = settings.get("global_proxy", "").strip()
        if global_proxy:
            os.environ["HTTP_PROXY"] = global_proxy
            os.environ["HTTPS_PROXY"] = global_proxy

        try:
            webbrowser.open(target_url)
            if self.context.get("log"):
                self.context["log"](f"已使用 [{engine}] 引擎检索软件: {app_name}")
            return {"success": True, "url": target_url}
        except Exception as e:
            return {"success": False, "msg": str(e)}
