import os
import sys
import time
import threading
import subprocess
import ctypes
import tkinter as tk
from tkinter import ttk, messagebox
import psutil
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False
class GPUFrequencyBoosterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NVIDIA 显卡特定程序锁定高频工具")
        self.root.geometry("520x480")
        self.root.resizable(False, False)
        self.monitoring = False
        self.freq_locked = False
        self.target_process_name = ""
        self.create_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    def create_widgets(self):
        admin_status = "【已获得管理员权限】" if is_admin() else "【警告：未以管理员权限运行，锁频将无效！】"
        admin_color = "green" if is_admin() else "red"
        lbl_admin = tk.Label(self.root, text=admin_status, fg=admin_color, font=("微软雅黑", 10, "bold"))
        lbl_admin.pack(pady=5)
        frame_select = tk.LabelFrame(self.root, text=" 1. 选择目标程序 ", font=("微软雅黑", 10), padx=10, pady=10)
        frame_select.pack(fill="x", padx=15, pady=5)
        btn_refresh = tk.Button(frame_select, text="刷新运行中的程序列表", command=self.refresh_process_list)
        btn_refresh.pack(anchor="w", pady=2)
        self.combo_processes = ttk.Combobox(frame_select, state="readonly", width=55)
        self.combo_processes.pack(fill="x", pady=5)
        frame_freq = tk.LabelFrame(self.root, text=" 2. 锁定频率设置 (MHz) ", font=("微软雅黑", 10), padx=10, pady=10)
        frame_freq.pack(fill="x", padx=15, pady=5)
        lbl_freq = tk.Label(frame_freq, text="目标核心频率 (默认 2200 MHz):")
        lbl_freq.pack(side="left", padx=5)
        self.entry_freq = tk.Entry(frame_freq, width=12)
        self.entry_freq.insert(0, "2200")
        self.entry_freq.pack(side="left", padx=5)
        frame_control = tk.Frame(self.root, pady=10)
        frame_control.pack()
        self.btn_toggle = tk.Button(
            frame_control,
            text="开始自动提频监控",
            bg="#4CAF50",
            fg="white",
            font=("微软雅黑", 11, "bold"),
            width=20,
            command=self.toggle_monitoring
        )
        self.btn_toggle.pack()
        self.lbl_status = tk.Label(self.root, text="状态: 闲置中", fg="gray", font=("微软雅黑", 10))
        self.lbl_status.pack(pady=5)
        self.txt_log = tk.Text(self.root, height=8, width=65, state="disabled", font=("Consolas", 9))
        self.txt_log.pack(padx=15, pady=5)
        self.refresh_process_list()
    def log(self, message):
        self.txt_log.config(state="normal")
        self.txt_log.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.txt_log.see(tk.END)
        self.txt_log.config(state="disabled")
    def refresh_process_list(self):
        processes = set()
        for proc in psutil.process_iter(['name']):
            try:
                name = proc.info['name']
                if name and name.endswith('.exe'):
                    processes.add(name)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        sorted_procs = sorted(list(processes), key=lambda s: s.lower())
        self.combo_processes['values'] = sorted_procs
        osu_found = [p for p in sorted_procs if "osu" in p.lower()]
        if osu_found:
            self.combo_processes.set(osu_found[0])
        elif sorted_procs:
            self.combo_processes.current(0)
        self.log("已刷新运行程序列表。")
    def set_gpu_clock(self, freq):
        try:
            cmd = f"nvidia-smi -lgc {freq},{freq}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                self.freq_locked = True
                self.log(f"成功锁定 GPU 核心频率在: {freq} MHz")
                self.lbl_status.config(text=f"状态: 运行中 (GPU 已锁定 {freq}MHz)", fg="green")
            else:
                self.log(f"锁频失败: {result.stderr.strip()}")
        except Exception as e:
            self.log(f"执行命令异常: {str(e)}")
    def reset_gpu_clock(self):
        try:
            cmd = "nvidia-smi -rgc"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                self.freq_locked = False
                self.log("已恢复 GPU 默认自动调频策略。")
                self.lbl_status.config(text="状态: 监控中 (等待目标程序启动)", fg="blue")
            else:
                self.log(f"恢复频率失败: {result.stderr.strip()}")
        except Exception as e:
            self.log(f"执行命令异常: {str(e)}")
    def toggle_monitoring(self):
        if not self.monitoring:
            target = self.combo_processes.get().strip()
            if not target:
                messagebox.showwarning("提示", "请先选择一个目标程序！")
                return
            if not is_admin():
                messagebox.showerror("错误", "请以管理员身份重新运行此 Python 脚本，否则无法修改显卡频率！")
                return
            self.target_process_name = target
            self.monitoring = True
            self.btn_toggle.config(text="停止监控并恢复", bg="#f44336")
            self.lbl_status.config(text="状态: 监控中...", fg="blue")
            self.log(f"已开启对 [{self.target_process_name}] 的监控。")
            threading.Thread(target=self.monitor_loop, daemon=True).start()
        else:
            self.monitoring = False
            self.btn_toggle.config(text="开始自动提频监控", bg="#4CAF50")
            if self.freq_locked:
                self.reset_gpu_clock()
            self.lbl_status.config(text="状态: 已停止监控", fg="gray")
            self.log("已停止监控。")
    def monitor_loop(self):
        while self.monitoring:
            is_running = any(
                p.info['name'].lower() == self.target_process_name.lower()
                for p in psutil.process_iter(['name'])
            )
            if is_running and not self.freq_locked:
                target_freq = self.entry_freq.get().strip()
                self.log(f"检测到 [{self.target_process_name}] 正在运行，开始提频...")
                self.set_gpu_clock(target_freq)
            elif not is_running and self.freq_locked:
                self.log(f"检测到 [{self.target_process_name}] 已关闭，还原显卡频率...")
                self.reset_gpu_clock()

            time.sleep(2)
    def on_closing(self):
        if self.freq_locked:
            self.reset_gpu_clock()
        self.root.destroy()
if __name__ == "__main__":
    root = tk.Tk()
    app = GPUFrequencyBoosterApp(root)
    root.mainloop()