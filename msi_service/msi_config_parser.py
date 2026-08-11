import os
import re


class MSIConfigParser:
    """负责读取与解析 MSI Afterburner 的配置文件及预设"""

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

        localappdata = os.path.expandvars(r"%LOCALAPPDATA%\MSI Afterburner")
        config_path = os.path.join(localappdata, "Profiles", "MSIAfterburner.cfg")
        if os.path.exists(config_path):
            return config_path

        return None

    def _parse_profile(self, content: str, profile_num: int) -> dict:
        profile_name = f"Profile{profile_num}"

        name_pattern = rf'Profile{profile_num}Name=(.+)'
        name_match = re.search(name_pattern, content)
        if name_match:
            profile_name = name_match.group(1).strip()

        core_clock = self._extract_value(content, rf'Profile{profile_num}CoreClock=(-?\d+)')
        memory_clock = self._extract_value(content, rf'Profile{profile_num}MemoryClock=(-?\d+)')
        core_voltage = self._extract_value(content, rf'Profile{profile_num}CoreVoltage=(-?\d+)')
        power_limit = self._extract_value(content, rf'Profile{profile_num}PowerLimit=(-?\d+)')
        temp_limit = self._extract_value(content, rf'Profile{profile_num}TempLimit=(-?\d+)')
        fan_speed = self._extract_value(content, rf'Profile{profile_num}FanSpeed=(-?\d+)')

        return {
            'id': profile_num,
            'name': profile_name,
            'core_clock': core_clock if core_clock is not None else 0,
            'memory_clock': memory_clock if memory_clock is not None else 0,
            'core_voltage': core_voltage if core_voltage is not None else 0,
            'power_limit': power_limit if power_limit is not None else 0,
            'temp_limit': temp_limit if temp_limit is not None else 0,
            'fan_speed': fan_speed if fan_speed is not None else 0
        }

    @staticmethod
    def _extract_value(content: str, pattern: str) -> int | None:
        match = re.search(pattern, content)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                return None
        return None

    @staticmethod
    def _create_default_profiles() -> list[dict]:
        return [
            {'id': 1, 'name': '默认配置', 'core_clock': 0, 'memory_clock': 0, 'core_voltage': 0, 'power_limit': 0, 'temp_limit': 0, 'fan_speed': 0},
            {'id': 2, 'name': '超频配置1', 'core_clock': 100, 'memory_clock': 200, 'core_voltage': 0, 'power_limit': 100, 'temp_limit': 83, 'fan_speed': 60},
            {'id': 3, 'name': '超频配置2', 'core_clock': 150, 'memory_clock': 300, 'core_voltage': 50, 'power_limit': 110, 'temp_limit': 85, 'fan_speed': 70},
            {'id': 4, 'name': '静音配置', 'core_clock': -50, 'memory_clock': 0, 'core_voltage': -20, 'power_limit': 80, 'temp_limit': 75, 'fan_speed': 40},
            {'id': 5, 'name': '性能配置', 'core_clock': 200, 'memory_clock': 500, 'core_voltage': 100, 'power_limit': 120, 'temp_limit': 88, 'fan_speed': 80}
        ]

    @staticmethod
    def get_profile_summary(profile: dict | None) -> str:
        if not profile:
            return "无配置"

        parts = []
        if profile.get('core_clock', 0) != 0:
            parts.append(f"核心{profile['core_clock']:+d}MHz")
        if profile.get('memory_clock', 0) != 0:
            parts.append(f"显存{profile['memory_clock']:+d}MHz")
        if profile.get('core_voltage', 0) != 0:
            parts.append(f"电压{profile['core_voltage']:+d}mV")
        if profile.get('power_limit', 0) != 0:
            parts.append(f"功耗{profile['power_limit']}%")
        if profile.get('fan_speed', 0) != 0:
            parts.append(f"风扇{profile['fan_speed']}%")

        return " | ".join(parts) if parts else "默认设置"