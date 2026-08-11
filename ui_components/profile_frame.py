import tkinter as tk
from tkinter import ttk


class ProfileFrame(tk.LabelFrame):
    """配置方案管理面板"""
    def __init__(self, parent, controller):
        super().__init__(parent, text=" 1. 配置管理 ", font=("微软雅黑", 10), padx=10, pady=8)
        self.controller = controller

        row_profile_select = tk.Frame(self)
        row_profile_select.pack(fill="x", pady=2)

        tk.Label(row_profile_select, text="当前配置:").pack(side="left", padx=5)
        self.combo_profiles = ttk.Combobox(row_profile_select, state="readonly", width=25)
        self.combo_profiles.pack(side="left", padx=5)
        self.combo_profiles.bind("<<ComboboxSelected>>", self.controller.on_profile_selected)

        row_profile_btns = tk.Frame(self)
        row_profile_btns.pack(fill="x", pady=4)

        tk.Button(row_profile_btns, text="创建新配置", command=self.controller.create_new_profile, width=11).pack(side="left", padx=4)
        tk.Button(row_profile_btns, text="重命名配置", command=self.controller.rename_current_profile, width=11).pack(side="left", padx=4)
        tk.Button(row_profile_btns, text="删除当前配置", command=self.controller.delete_current_profile, width=11).pack(side="left", padx=4)
        tk.Button(row_profile_btns, text="从控制面板/已安装应用导入", command=self.controller.open_import_dialog, width=22, bg="#E8EAF6").pack(side="right", padx=4)