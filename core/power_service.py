import subprocess
import re
import sys


class PowerPlanService:
    """Windows 电源计划查询与切换服务"""

    @classmethod
    def get_power_plans(cls):
        plans = []
        if sys.platform != "win32":
            return plans
        try:
            creation_flags = 0x08000000 if sys.platform == "win32" else 0
            res = subprocess.run(["powercfg", "/list"], capture_output=True, text=True, timeout=5, creationflags=creation_flags)
            if res.returncode == 0:
                pattern = r"GUID:\s+([a-fA-F0-9\-]+)\s+\(([^\)]+)\)(\s+\*)?"
                matches = re.findall(pattern, res.stdout)
                for guid, name, active in matches:
                    plans.append({
                        "guid": guid.strip(),
                        "name": name.strip(),
                        "is_active": bool(active and "*" in active)
                    })
        except Exception:
            pass
        return plans

    @classmethod
    def set_active_plan(cls, guid):
        if sys.platform != "win32" or not guid:
            return False, "无效的电源计划 GUID"
        try:
            creation_flags = 0x08000000 if sys.platform == "win32" else 0
            res = subprocess.run(f"powercfg /setactive {guid}", shell=True, capture_output=True, text=True, creationflags=creation_flags)
            if res.returncode == 0:
                return True, f"已切换电源计划为 [{guid}]"
            return False, f"切换电源计划失败: {res.stderr.strip()}"
        except Exception as e:
            return False, str(e)

    @classmethod
    def get_active_plan_guid(cls):
        plans = cls.get_power_plans()
        for p in plans:
            if p["is_active"]:
                return p["guid"]
        return None
