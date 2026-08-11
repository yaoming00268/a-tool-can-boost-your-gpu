from .msi_finder import MSIFinder
from .msi_config_parser import MSIConfigParser
from .msi_interactor import MSIInteractor


class MSIAfterburnerService:
    def __init__(self):
        self.install_path = MSIFinder.find_install_path()
        self.parser = MSIConfigParser(self.install_path)
        self.profiles = self.parser.load_profiles()

    def get_profiles(self) -> list[dict]:
        return self.profiles

    def get_profile_names(self) -> list[str]:
        return [p['name'] for p in self.profiles]

    def get_profile_by_name(self, name: str) -> dict | None:
        for profile in self.profiles:
            if profile['name'] == name:
                return profile
        return None

    def get_profile_by_id(self, profile_id: int) -> dict | None:
        for profile in self.profiles:
            if profile['id'] == profile_id:
                return profile
        return None

    def is_installed(self) -> bool:
        return self.install_path is not None

    def get_install_path(self) -> str | None:
        return self.install_path

    def is_running(self) -> bool:
        return MSIInteractor.is_running()

    def launch_afterburner(self) -> tuple[bool, str]:
        return MSIInteractor.launch_afterburner(self.install_path)

    def open_curve_editor(self) -> tuple[bool, str]:
        return MSIInteractor.open_curve_editor(self.install_path)

    def apply_profile(self, profile_id: int | str) -> tuple[bool, str]:
        return MSIInteractor.apply_profile(self.install_path, profile_id)

    def get_profile_summary(self, profile: dict | None) -> str:
        return MSIConfigParser.get_profile_summary(profile)

    def get_status_message(self) -> str:
        if self.is_installed():
            if self.is_running():
                return f"微星小飞机已就绪 [{self.get_install_path()}]"
            else:
                return f"微星小飞机已安装但未运行 [{self.get_install_path()}]"
        else:
            return "未检测到微星小飞机安装，MSI配置功能不可用"