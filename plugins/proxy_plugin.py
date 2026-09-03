import re
from plugins.base_plugin import BasePlugin


class ProxyPlugin(BasePlugin):
    plugin_id = "proxy"
    plugin_name = "网络代理格式校验插件"
    order = 20

    def get_api_methods(self):
        return {
            "validate_proxy": self.validate_proxy
        }

    def validate_proxy(self, proxy_str):
        if not proxy_str or not proxy_str.strip():
            return True
        pattern = r"^(http|https|socks4|socks5)://[a-zA-Z0-9.\-_]+:\d{1,5}$"
        return bool(re.match(pattern, proxy_str.strip(), re.IGNORECASE))
