import importlib
import inspect
import os
import pkgutil
from plugins.base_plugin import BasePlugin


class PluginManager:
    def __init__(self, context):
        self.context = context
        self.plugins: list[BasePlugin] = []
        self.api_registry: dict = {}

    def discover_and_load(self):
        import plugins
        self.plugins.clear()
        self.api_registry.clear()

        pkg_path = os.path.dirname(plugins.__file__)
        for _, module_name, _ in pkgutil.iter_modules([pkg_path]):
            if module_name in ["base_plugin", "plugin_manager"]:
                continue
            module = importlib.import_module(f"plugins.{module_name}")
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if inspect.isclass(attr) and issubclass(attr, BasePlugin) and attr is not BasePlugin:
                    instance = attr(self.context)
                    instance.on_init()
                    self.plugins.append(instance)
                    for name, method in instance.get_api_methods().items():
                        self.api_registry[name] = method

        self.plugins.sort(key=lambda p: p.order)

    def dispatch(self, action_name: str, *args):
        func = self.api_registry.get(action_name)
        if func:
            return func(*args)
        return None

    def notify_shutdown(self):
        for p in self.plugins:
            try:
                p.on_shutdown()
            except Exception:
                pass
