# ui_app/msi_controller.py
import threading
from tkinter import messagebox


class MSIController:
    def __init__(self, app):
        self.app = app

    def check_msi_afterburner(self):
        msi = self.app.msi_service
        if msi and msi.is_installed():
            self.app.log(f"已检测到微星小飞机: {msi.get_install_path()}")
            if msi.is_running():
                self.app.admin_frame.set_msi_status("[MSI 已就绪]", "green")
            else:
                self.app.admin_frame.set_msi_status("[MSI 未运行]", "orange")
        else:
            self.app.admin_frame.set_msi_status("[MSI 未安装]", "gray")

    def load_msi_profiles(self):
        msi = self.app.msi_service
        if msi:
            self.app.rule_frame.set_msi_profiles(msi.get_profile_names())
            self.app.combo_msi_profile.bind("<<ComboboxSelected>>", self.on_msi_profile_selected)

    def on_msi_profile_selected(self, event=None):
        msi = self.app.msi_service
        if not msi: return
        profile_name = self.app.combo_msi_profile.get()
        if profile_name and profile_name != "默认配置":
            profile = msi.get_profile_by_name(profile_name)
            self.app.lbl_msi_info.config(text=msi.get_profile_summary(profile) if profile else "")
        else:
            self.app.lbl_msi_info.config(text="使用默认设置")

    def open_msi_vf_editor(self):
        """唤醒微星小飞机并按 Ctrl+F 激活 Curve Editor"""
        msi = self.app.msi_service
        if not msi or not msi.is_installed():
            messagebox.showinfo("提示", "未检测到微星小飞机 (MSI Afterburner) 安装。")
            return

        def async_task():
            self.app.log("正在尝试唤醒微星小飞机并调出 Curve Editor...")
            success, msg = msi.open_curve_editor()
            self.app.log(msg)

        threading.Thread(target=async_task, daemon=True).start()

    def apply_selected_msi_profile(self):
        selected = self.app.tree_rules.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择要应用MSI配置的规则")
            return
        active_profile = self.app.combo_profiles.get().strip()
        proc_name = self.app.tree_rules.item(selected[0])['text'].strip()
        msi_profile = self.app.combo_msi_profile.get()

        if self.app.config_mgr.update_rule_msi_profile(active_profile, proc_name, msi_profile):
            self.app.profile_rule_ctrl.load_tree_rules()
            self.app.log(f"规则 [{proc_name}] 已关联微星小飞机配置: {msi_profile}")
            if msi_profile != "默认配置" and self.app.msi_service and self.app.msi_service.is_installed():
                profile = self.app.msi_service.get_profile_by_name(msi_profile)
                if profile:
                    success, msg = self.app.msi_service.apply_profile(profile['id'])
                    self.app.log(msg)
        else:
            messagebox.showerror("错误", "更新MSI配置失败")