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

    def is_installed(self) -> bool:
        return self.install_path is not None

    def is_running(self) -> bool:
        return MSIInteractor.is_running()

    def launch_afterburner(self) -> tuple[bool, str]:
        return MSIInteractor.launch_afterburner(self.install_path)

    def open_curve_editor(self) -> tuple[bool, str]:
        return MSIInteractor.open_curve_editor(self.install_path)

    def apply_profile(self, profile_id: int | str) -> tuple[bool, str]:
        return MSIInteractor.apply_profile(self.install_path, profile_id)
