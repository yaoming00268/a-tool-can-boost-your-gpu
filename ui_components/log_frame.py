import time
import tkinter as tk


class LogFrame(tk.LabelFrame):
    """文本日志输出面板"""
    def __init__(self, parent):
        super().__init__(parent, text=" 运行日志 ", font=("微软雅黑", 10), padx=5, pady=5)
        self.txt_log = tk.Text(self, state="disabled", font=("Consolas", 9), height=7)
        self.txt_log.pack(fill="both", expand=True)

    def append_log(self, message):
        self.txt_log.config(state="normal")
        t_str = time.strftime("%H:%M:%S")
        self.txt_log.insert(tk.END, f"[{t_str}] {message}\n")
        self.txt_log.see(tk.END)
        self.txt_log.config(state="disabled")