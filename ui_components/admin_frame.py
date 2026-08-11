import tkinter as tk
from gpu_service import is_admin


class AdminFrame(tk.Frame):
    """管理员权限指示与微星小飞机状态显示栏"""
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        left_frame = tk.Frame(self)
        left_frame.pack(side="left", fill="y")

        admin_text = "[管理员权限已就绪]" if is_admin() else "[警告: 未获得管理员权限，锁定频率功能将不可用]"
        admin_color = "green" if is_admin() else "red"
        self.lbl_admin = tk.Label(left_frame, text=admin_text, fg=admin_color, font=("微软雅黑", 10, "bold"))
        self.lbl_admin.pack(side="left", padx=5)

        if not is_admin():
            self.btn_elevate = tk.Button(
                left_frame,
                text="自动获取管理员权限",
                command=self.controller.request_admin_privileges,
                bg="#FFCC80",
                font=("微软雅黑", 9, "bold")
            )
            self.btn_elevate.pack(side="left", padx=5)

        self.lbl_msi_status = tk.Label(self, text="", font=("微软雅黑", 9))
        self.lbl_msi_status.pack(side="right", padx=5)

    def set_msi_status(self, text, color="gray"):
        """设置微星小飞机状态显示"""
        self.lbl_msi_status.config(text=text, fg=color)