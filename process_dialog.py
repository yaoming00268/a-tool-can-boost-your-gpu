import threading
import tkinter as tk
from tkinter import ttk
import psutil

from icon_helper import IconHelper


class ProcessSearchDialog(tk.Toplevel):
    """搜索与选择当前运行进程对话框"""

    def __init__(self, parent, on_select_callback):
        super().__init__(parent)
        self.title("搜索与选择运行中的程序进程")
        self.geometry("560x480")
        self.transient(parent)
        self.grab_set()

        self.on_select_callback = on_select_callback
        self.processes = []
        self.icon_references = []

        self.create_widgets()
        self.load_running_processes()

    def create_widgets(self):
        frame_search = tk.Frame(self, pady=5, padx=10)
        frame_search.pack(fill="x")

        tk.Label(frame_search, text="搜索进程:", font=("微软雅黑", 9)).pack(side="left", padx=5)
        self.var_search = tk.StringVar()
        self.var_search.trace_add("write", self.filter_processes)
        entry_search = tk.Entry(frame_search, textvariable=self.var_search, font=("微软雅黑", 9))
        entry_search.pack(side="left", fill="x", expand=True, padx=5)

        frame_tree = tk.Frame(self, padx=10, pady=5)
        frame_tree.pack(fill="both", expand=True)

        scroll = ttk.Scrollbar(frame_tree)
        scroll.pack(side="right", fill="y")

        self.tree = ttk.Treeview(
            frame_tree,
            columns=("pid", "path"),
            show="tree headings",
            yscrollcommand=scroll.set,
            selectmode="browse"
        )
        scroll.config(command=self.tree.yview)

        self.tree.heading("#0", text="进程文件名 (.exe)", anchor="w")
        self.tree.heading("pid", text="PID", anchor="center")
        self.tree.heading("path", text="程序路径", anchor="w")

        self.tree.column("#0", width=220, anchor="w")
        self.tree.column("pid", width=80, anchor="center")
        self.tree.column("path", width=220, anchor="w")

        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", self.on_double_click)

        frame_btns = tk.Frame(self, pady=8, padx=10)
        frame_btns.pack(fill="x")

        btn_confirm = tk.Button(
            frame_btns,
            text="选择该进程",
            bg="#4CAF50",
            fg="white",
            font=("微软雅黑", 9, "bold"),
            command=self.confirm_selection
        )
        btn_confirm.pack(side="right", padx=5)

        btn_cancel = tk.Button(frame_btns, text="取消", command=self.destroy)
        btn_cancel.pack(side="right", padx=5)

    def load_running_processes(self):
        def scan():
            procs = []
            seen = set()
            for p in psutil.process_iter(["pid", "name", "exe"]):
                try:
                    name = p.info["name"]
                    pid = p.info["pid"]
                    exe = p.info["exe"] or ""
                    if name and name.lower().endswith(".exe"):
                        key = (name.lower(), exe.lower())
                        if key not in seen:
                            seen.add(key)
                            procs.append({"name": name, "pid": pid, "exe": exe})
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            procs.sort(key=lambda x: x["name"].lower())
            self.processes = procs
            self.after(0, lambda: self.populate_tree(procs))

        threading.Thread(target=scan, daemon=True).start()

    def populate_tree(self, procs):
        self.tree.delete(*self.tree.get_children())
        self.icon_references.clear()

        for proc in procs:
            icon = IconHelper.get_icon(proc["exe"])
            self.icon_references.append(icon)
            self.tree.insert(
                "",
                tk.END,
                text=" " + proc["name"],
                image=icon,
                values=(proc["pid"], proc["exe"])
            )

    def filter_processes(self, *args):
        query = self.var_search.get().strip().lower()
        if not query:
            self.populate_tree(self.processes)
            return

        filtered = [
            p for p in self.processes
            if query in p["name"].lower() or query in p["exe"].lower()
        ]
        self.populate_tree(filtered)

    def on_double_click(self, event):
        self.confirm_selection()

    def confirm_selection(self):
        selected = self.tree.selection()
        if not selected:
            return

        item = self.tree.item(selected[0])
        proc_name = item["text"].strip()
        if proc_name:
            self.on_select_callback(proc_name)
            self.destroy()