import threading
import tkinter as tk
from tkinter import messagebox, ttk

from app_scanner import AppScanner
from icon_helper import IconHelper


class ImportAppsDialog(tk.Toplevel):
    """从控制面板 / 已安装应用程序导入规则对话框"""

    def __init__(self, parent, active_profile_name, on_import_callback):
        super().__init__(parent)
        self.title("从控制面板与已安装程序导入规则")
        self.geometry("620x540")
        self.transient(parent)
        self.grab_set()

        self.active_profile_name = active_profile_name
        self.on_import_callback = on_import_callback
        self.installed_apps = []
        self.filtered_apps = []
        self.icon_references = []

        self.create_widgets()
        self.load_installed_apps()

    def create_widgets(self):
        frame_search = tk.Frame(self, pady=6, padx=10)
        frame_search.pack(fill="x")

        tk.Label(frame_search, text="搜索应用名称或路径:", font=("微软雅黑", 9)).pack(side="left", padx=5)
        self.var_search = tk.StringVar()
        self.var_search.trace_add("write", self.filter_apps)
        entry_search = tk.Entry(frame_search, textvariable=self.var_search, font=("微软雅黑", 9))
        entry_search.pack(side="left", fill="x", expand=True, padx=5)

        frame_tree = tk.Frame(self, padx=10, pady=5)
        frame_tree.pack(fill="both", expand=True)

        scroll = ttk.Scrollbar(frame_tree)
        scroll.pack(side="right", fill="y")

        self.tree = ttk.Treeview(
            frame_tree,
            columns=("exe_name", "exe_path"),
            show="tree headings",
            yscrollcommand=scroll.set,
            selectmode="extended"
        )
        scroll.config(command=self.tree.yview)

        self.tree.heading("#0", text="控制面板软件名称", anchor="w")
        self.tree.heading("exe_name", text="可执行文件名 (.exe)", anchor="w")
        self.tree.heading("exe_path", text="可执行程序文件绝对路径", anchor="w")

        self.tree.column("#0", width=220, anchor="w")
        self.tree.column("exe_name", width=150, anchor="w")
        self.tree.column("exe_path", width=210, anchor="w")

        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", self.on_double_click)

        frame_action = tk.Frame(self, pady=10, padx=10)
        frame_action.pack(fill="x")

        tk.Label(frame_action, text="导入锁频 (MHz):").pack(side="left", padx=5)
        self.entry_freq = tk.Entry(frame_action, width=10)
        self.entry_freq.insert(0, "2200")
        self.entry_freq.pack(side="left", padx=5)

        btn_import = tk.Button(
            frame_action,
            text="确认导入选中应用",
            bg="#4CAF50",
            fg="white",
            font=("微软雅黑", 9, "bold"),
            command=self.confirm_import
        )
        btn_import.pack(side="right", padx=5)

        btn_cancel = tk.Button(frame_action, text="取消", command=self.destroy)
        btn_cancel.pack(side="right", padx=5)

    def load_installed_apps(self):
        def scan():
            apps = AppScanner.get_installed_apps()
            self.installed_apps = apps
            self.after(0, lambda: self.populate_tree(apps))

        threading.Thread(target=scan, daemon=True).start()

    def populate_tree(self, apps):
        self.tree.delete(*self.tree.get_children())
        self.icon_references.clear()

        for app in apps:
            path_or_name = app["exe_path"] if app["exe_path"] else app["exe_name"]
            icon = IconHelper.get_icon(path_or_name)
            self.icon_references.append(icon)
            self.tree.insert(
                "",
                tk.END,
                text=" " + app["name"],
                image=icon,
                values=(app["exe_name"], app["exe_path"])
            )

    def filter_apps(self, *args):
        query = self.var_search.get().strip().lower()
        if not query:
            self.populate_tree(self.installed_apps)
            return

        filtered = [
            app for app in self.installed_apps
            if query in app["name"].lower() or query in app["exe_name"].lower() or query in app["exe_path"].lower()
        ]
        self.populate_tree(filtered)

    def on_double_click(self, event):
        self.confirm_import()

    def confirm_import(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("提示", "请先选择要导入的应用程序", parent=self)
            return

        freq_str = self.entry_freq.get().strip()
        try:
            freq = int(freq_str)
            if freq <= 0 or freq > 4000:
                raise ValueError("频率超出合理范围")
        except ValueError:
            messagebox.showerror("错误", "请输入有效的正整数频率 (1-4000 MHz)", parent=self)
            return

        imported_count = 0
        for item_id in selected_items:
            values = self.tree.item(item_id, "values")
            if values and values[0]:
                exe_name = values[0]
                self.on_import_callback(exe_name, freq)
                imported_count += 1

        messagebox.showinfo("成功", f"已成功导入 {imported_count} 个应用程序规则！", parent=self)
        self.destroy()