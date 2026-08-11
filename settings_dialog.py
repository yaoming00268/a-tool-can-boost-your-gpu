import tkinter as tk
from tkinter import ttk, messagebox


class SettingsDialog(tk.Toplevel):
    """软件系统设置窗口"""

    def __init__(self, parent, config_mgr, on_save_callback):
        super().__init__(parent)
        self.title("软件设置")
        self.geometry("380x280")
        # 移除 self.transient(parent) 解除窗口拖动限制
        self.grab_set()

        self.config_mgr = config_mgr
        self.on_save_callback = on_save_callback
        self.settings = self.config_mgr.get_settings()

        self.create_widgets()

    def create_widgets(self):
        frame = tk.Frame(self, padx=20, pady=20)
        frame.pack(fill="both", expand=True)

        self.var_autostart = tk.BooleanVar(value=self.settings.get("auto_start", False))
        chk_autostart = tk.Checkbutton(frame, text="开机自启 (跟随 Windows 启动)", variable=self.var_autostart,
                                       font=("微软雅黑", 10))
        chk_autostart.pack(anchor="w", pady=10)

        frame_profile = tk.Frame(frame)
        frame_profile.pack(fill="x", pady=10)
        tk.Label(frame_profile, text="开机自动启用配置: ", font=("微软雅黑", 10)).pack(side="left")

        self.combo_profile = ttk.Combobox(frame_profile, state="readonly", width=18)
        profiles = ["不自动启用"] + self.config_mgr.get_profile_names()
        self.combo_profile["values"] = profiles
        current_auto = self.settings.get("auto_profile", "不自动启用")
        if current_auto in profiles:
            self.combo_profile.set(current_auto)
        else:
            self.combo_profile.current(0)
        self.combo_profile.pack(side="left", padx=5)

        frame_hotkey = tk.Frame(frame)
        frame_hotkey.pack(fill="x", pady=10)
        tk.Label(frame_hotkey, text="启停监控快捷键: ", font=("微软雅黑", 10)).pack(side="left")

        self.combo_hotkey = ttk.Combobox(frame_hotkey, state="readonly", width=18)
        self.combo_hotkey["values"] = ["无", "F12", "Ctrl+F12", "Alt+F12", "HOME", "END"]
        current_hotkey = self.settings.get("hotkey", "F12")
        if current_hotkey in self.combo_hotkey["values"]:
            self.combo_hotkey.set(current_hotkey)
        else:
            self.combo_hotkey.set("F12")
        self.combo_hotkey.pack(side="left", padx=5)

        btn_frame = tk.Frame(frame)
        btn_frame.pack(fill="x", pady=20)
        tk.Button(btn_frame, text="保存并应用", command=self.save_settings, bg="#4CAF50", fg="white", width=12).pack(
            side="right")
        tk.Button(btn_frame, text="取消", command=self.destroy, width=10).pack(side="right", padx=10)

    def save_settings(self):
        new_settings = {
            "auto_start": self.var_autostart.get(),
            "auto_profile": self.combo_profile.get(),
            "hotkey": self.combo_hotkey.get()
        }
        self.config_mgr.save_settings(new_settings)
        self.on_save_callback()
        messagebox.showinfo("成功", "设置已成功保存并应用！", parent=self)
        self.destroy()