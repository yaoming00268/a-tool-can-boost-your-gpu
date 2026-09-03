from abc import ABC


class BasePlugin(ABC):
    plugin_id: str = "base"
    plugin_name: str = "Base Plugin"
    order: int = 100

    def __init__(self, context):
        self.context = context

    def on_init(self):
        pass

    def on_shutdown(self):
        pass

    def get_api_methods(self) -> dict:
        return {}
