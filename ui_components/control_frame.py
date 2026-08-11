# ui_components/control_frame.py
import tkinter as tk


class ControlFrame(tk.LabelFrame):
    """监控启停与系统功能调用面板"""
    def __init__(self, parent, controller, config_mgr):
        super().__init__(parent, text=" 3. 监控服务与 PC 调频策略 ", font=("微软雅黑", 10), padx=10, pady=8)
        self.controller = controller

        self.var_only_foreground = tk.BooleanVar(value=config_mgr.get_only_foreground())
        chk_foreground = tk.Checkbutton(
            self,
            text="仅前台活动窗口生效 (自动检测当前获得焦点的前台窗口)",
            variable=self.var_only_foreground,
            command=self.controller.on_only_foreground_changed,
            font=("微软雅黑", 9)
        )
        chk_foreground.pack(anchor="w", padx=5, pady=2)

        row_ctrl_btns = tk.Frame(self)
        row_ctrl_btns.pack(fill="x", pady=4)

        self.btn_toggle = tk.Button(
            row_ctrl_btns,
            text="启动自动提频监控",
            bg="#4CAF50",
            fg="white",
            font=("微软雅黑", 10, "bold"),
            height=1,
            command=self.controller.toggle_monitoring
        )
        self.btn_toggle.pack(side="left", fill="x", expand=True, padx=4)

        btn_msi_vf = tk.Button(
            row_ctrl_btns,
            text="打开小飞机 V-F 曲线",
            bg="#0288D1",
            fg="white",
            font=("微软雅黑", 10, "bold"),
            height=1,
            command=self.controller.open_msi_vf_editor
        )
        btn_msi_vf.pack(side="left", padx=4)

        btn_taskmgr = tk.Button(
            row_ctrl_btns,
            text="打开任务管理器",
            bg="#009688",
            fg="white",
            font=("微软雅黑", 10, "bold"),
            height=1,
            command=self.controller.open_task_manager
        )
        btn_taskmgr.pack(side="right", padx=4)

        self.lbl_status = tk.Label(self, text="状态: 服务空闲", fg="gray", font=("微软雅黑", 10))
        self.lbl_status.pack(pady=4)