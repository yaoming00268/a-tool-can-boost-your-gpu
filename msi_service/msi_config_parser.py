import os
import re


class MSIConfigParser:
    DEFAULT_PROFILE_COUNT = 5

    def __init__(self, install_path: str | None):
        self.install_path = install_path

    def load_profiles(self) -> list[dict]:
        config_path = self._get_config_path()
        if not config_path or not os.path.exists(config_path):
            return self._create_default_profiles()
        try:
            with open(config_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            profiles = []
            for i in range(1, self.DEFAULT_PROFILE_COUNT + 1):
                profile = self._parse_profile(content, i)
                if profile:
                    profiles.append(profile)
            return profiles if profiles else self._create_default_profiles()
        except Exception:
            return self._create_default_profiles()

    def _get_config_path(self) -> str | None:
        if self.install_path:
            config_path = os.path.join(self.install_path, "Profiles", "MSIAfterburner.cfg")
            if os.path.exists(config_path):
                return config_path
        appdata = os.path.expandvars(r"%APPDATA%\MSI Afterburner")
        config_path = os.path.join(appdata, "Profiles", "MSIAfterburner.cfg")
        if os.path.exists(config_path):
            return config_path
        return None

    def _parse_profile(self, content: str, profile_num: int) -> dict:
        profile_name = f"Profile{profile_num}"
        name_match = re.search(rf'Profile{profile_num}Name=(.+)', content)
        if name_match:
            profile_name = name_match.group(1).strip()

        return {
            'id': profile_num,
            'name': profile_name
        }

    @staticmethod
    def _create_default_profiles() -> list[dict]:
        return [
            {'id': 1, 'name': '默认配置'},
            {'id': 2, 'name': '超频配置1'},
            {'id': 3, 'name': '超频配置2'},
            {'id': 4, 'name': '静音配置'},
            {'id': 5, 'name': '性能配置'}
        ]
