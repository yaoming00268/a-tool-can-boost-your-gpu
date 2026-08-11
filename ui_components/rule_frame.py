import tkinter as tk
from tkinter import ttk


class RuleFrame(tk.LabelFrame):
    """程序频率规则配置与 Treeview 表格面板"""
    def __init__(self, parent, controller):
        super().__init__(parent, text=" 2. 程序频率规则配置 ", font=("微软雅黑", 10), padx=10, pady=8)
        self.controller = controller

        frame_rule_search = tk.Frame(self)
        frame_rule_search.pack(fill="x", pady=2)

        tk.Label(frame_rule_search, text="搜索当前规则:", font=("微软雅黑", 9)).pack(side="left", padx=2)
        self.var_rule_search = tk.StringVar()
        self.var_rule_search.trace_add("write", lambda *args: self.controller.load_tree_rules())
        entry_rule_search = tk.Entry(frame_rule_search, textvariable=self.var_rule_search, font=("微软雅黑", 9))
        entry_rule_search.pack(side="left", fill="x", expand=True, padx=4)

        tree_scroll = ttk.Scrollbar(self)
        tree_scroll.pack(side="right", fill="y")

        self.tree_rules = ttk.Treeview(
            self,
            columns=("mode", "frequency", "msi_profile"),
            show="tree headings",
            height=6,
            yscrollcommand=tree_scroll.set
        )
        tree_scroll.config(command=self.tree_rules.yview)

        self.tree_rules.heading("#0", text="程序进程名 (.exe)", anchor="w")
        self.tree_rules.heading("mode", text="调频模式", anchor="center")
        self.tree_rules.heading("frequency", text="频率参数 (MHz)", anchor="center")
        self.tree_rules.heading("msi_profile", text="MSI配置", anchor="center")
        self.tree_rules.column("#0", width=220, anchor="w")
        self.tree_rules.column("mode", width=80, anchor="center")
        self.tree_rules.column("frequency", width=150, anchor="center")
        self.tree_rules.column("msi_profile", width=150, anchor="center")
        self.tree_rules.pack(fill="x", pady=4)

        self.tree_rules.bind("<<TreeviewSelect>>", self.controller.on_rule_tree_selected)

        self.tree_menu = tk.Menu(self, tearoff=0)
        self.tree_menu.add_command(label="运行该程序", command=self.controller.launch_selected_rule)
        self.tree_menu.add_command(label="应用MSI配置", command=self.controller.apply_selected_msi_profile)
        self.tree_rules.bind("<Button-3>", self.show_tree_menu)

        frame_rule_input = tk.Frame(self)
        frame_rule_input.pack(fill="x", pady=2)

        tk.Label(frame_rule_input, text="程序:").grid(row=0, column=0, padx=2, sticky="w")
        self.combo_process_input = ttk.Combobox(frame_rule_input, width=18)
        self.combo_process_input.grid(row=0, column=1, padx=2)

        btn_search_proc = tk.Button(frame_rule_input, text="搜索进程", command=self.controller.open_process_search_dialog, bg="#FFF3E0")
        btn_search_proc.grid(row=0, column=2, padx=2)

        btn_detect_fg = tk.Button(frame_rule_input, text="前台窗口", command=self.controller.detect_foreground_window, bg="#E8F5E9")
        btn_detect_fg.grid(row=0, column=3, padx=2)

        tk.Label(frame_rule_input, text="模式:").grid(row=0, column=4, padx=2, sticky="w")
        self.combo_mode = ttk.Combobox(frame_rule_input, values=["定频模式", "频段模式"], state="readonly", width=8)
        self.combo_mode.current(0)
        self.combo_mode.grid(row=0, column=5, padx=2)

        frame_rule_input2 = tk.Frame(self)
        frame_rule_input2.pack(fill="x", pady=2)

        tk.Label(frame_rule_input2, text="定频:").grid(row=0, column=0, padx=2, pady=2, sticky="w")
        self.entry_freq_input = tk.Entry(frame_rule_input2, width=8)
        self.entry_freq_input.insert(0, "2200")
        self.entry_freq_input.grid(row=0, column=1, padx=2, pady=2, sticky="w")

        tk.Label(frame_rule_input2, text="频段下限:").grid(row=0, column=2, padx=2, pady=2, sticky="w")
        self.entry_min_freq = tk.Entry(frame_rule_input2, width=8)
        self.entry_min_freq.grid(row=0, column=3, padx=2, pady=2, sticky="w")

        tk.Label(frame_rule_input2, text="频段上限:").grid(row=0, column=4, padx=2, pady=2, sticky="w")
        self.entry_max_freq = tk.Entry(frame_rule_input2, width=8)
        self.entry_max_freq.grid(row=0, column=5, padx=2, pady=2, sticky="w")

        frame_msi = tk.Frame(self)
        frame_msi.pack(fill="x", pady=2)

        tk.Label(frame_msi, text="微星小飞机配置:", font=("微软雅黑", 9)).pack(side="left", padx=2)
        self.combo_msi_profile = ttk.Combobox(frame_msi, state="readonly", width=30)
        self.combo_msi_profile.pack(side="left", padx=4)
        self.lbl_msi_info = tk.Label(frame_msi, text="", font=("微软雅黑", 8), fg="#666666")
        self.lbl_msi_info.pack(side="left", padx=4)

        frame_rule_btns = tk.Frame(self)
        frame_rule_btns.pack(fill="x", pady=4)

        tk.Button(frame_rule_btns, text="添加 / 更新规则", command=self.controller.add_or_update_rule, width=16, bg="#E1F5FE").pack(side="left", padx=4)
        tk.Button(frame_rule_btns, text="删除选中规则", command=self.controller.delete_selected_rule, width=16, bg="#FFEBEE").pack(side="left", padx=4)
        tk.Button(frame_rule_btns, text="运行选中程序", command=self.controller.launch_selected_rule, width=16, bg="#E8F5E9").pack(side="left", padx=4)
        tk.Button(frame_rule_btns, text="清空输入", command=self.controller.clear_input_fields, width=12).pack(side="right", padx=4)

    def show_tree_menu(self, event):
        item = self.tree_rules.identify_row(event.y)
        if item:
            self.tree_rules.selection_set(item)
            self.tree_menu.tk_popup(event.x_root, event.y_root)

    def set_msi_profiles(self, profile_names):
        """设置微星小飞机配置列表"""
        values = ["默认配置"] + profile_names
        self.combo_msi_profile["values"] = values
        self.combo_msi_profile.set("默认配置")