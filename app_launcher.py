# app_launcher.py
import os
import sys
import subprocess
from icon_helper import IconHelper


class AppLauncher:
    """应用程序快捷启动器"""

    @staticmethod
    def launch_app(exe_name):
        path = IconHelper.resolve_path(exe_name)
        if path and os.path.exists(path):
            try:
                if sys.platform == "win32":
                    os.startfile(path)
                else:
                    subprocess.Popen([path])
                return True, f"已成功启动程序: {path}"
            except Exception as e:
                return False, f"程序启动失败: {str(e)}"
        return False, f"未能在系统中找到程序路径，无法启动: {exe_name}"