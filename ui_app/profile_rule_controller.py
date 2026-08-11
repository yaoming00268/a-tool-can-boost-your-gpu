import tkinter as tk
from tkinter import messagebox, simpledialog
from app_launcher import AppLauncher
from icon_helper import IconHelper


class ProfileRuleController:
    def __init__(self, app):
        self.app = app
        self.config_mgr = app.config_mgr

    def load_profile_list(self):
        names = self.config_mgr.get_profile_names()
        self.app.combo_profiles["values"] = names
        active = self.config_mgr.get_active_profile_name()
        if active in names:
            self.app.combo_profiles.set(active)
        elif names:
            self.app.combo_profiles.current(0)
            self.config_mgr.set_active_profile(names[0])
        self.load_tree_rules()

    def on_profile_selected(self, event=None):
        selected = self.app.combo_profiles.get().strip()
        if selected:
            self.config_mgr.set_active_profile(selected)
            self.load_tree_rules()
            self.app.log(f"已切换到配置: [{selected}]")

    def create_new_profile(self):
        name = simpledialog.askstring("创建配置", "请输入新配置名称:", parent=self.app.root)
        if name:
            success, msg = self.config_mgr.create_profile(name)
            if success:
                self.load_profile_list()
                self.app.log(msg)
            else:
                messagebox.showerror("错误", msg)

    def rename_current_profile(self):
        old_name = self.app.combo_profiles.get().strip()
        if not old_name: return
        new_name = simpledialog.askstring("重命名配置", f"请输入 [{old_name}] 的新名称:", parent=self.app.root)
        if new_name:
            success, msg = self.config_mgr.rename_profile(old_name, new_name)
            if success:
                self.load_profile_list()
                self.app.log(msg)
            else:
                messagebox.showerror("错误", msg)

    def delete_current_profile(self):
        current_name = self.app.combo_profiles.get().strip()
        if not current_name: return
        if messagebox.askyesno("确认删除", f"确定要删除配置 [{current_name}] 吗？", parent=self.app.root):
            success, msg = self.config_mgr.delete_profile(current_name)
            if success:
                self.load_profile_list()
                self.app.log(msg)
            else:
                messagebox.showerror("错误", msg)

    def load_tree_rules(self):
        for item in self.app.tree_rules.get_children():
            self.app.tree_rules.delete(item)
        self.app.rule_icons.clear()

        active = self.app.combo_profiles.get().strip()
        if not active: return

        query = self.app.var_rule_search.get().strip().lower()
        for rule in self.config_mgr.get_profile_rules(active):
            proc_name = rule["process"]
            mode = rule.get("mode", "定频模式")
            msi_profile = rule.get("msi_profile", None)
            freq_info = str(rule.get("frequency",
                                     2200)) if mode == "定频模式" else f"{rule.get('min_freq', 200)} - {rule.get('max_freq', 4000)}"
            msi_display = msi_profile if msi_profile else "默认配置"

            if query and query not in proc_name.lower(): continue
            icon = IconHelper.get_icon(proc_name)
            self.app.rule_icons.append(icon)
            self.app.tree_rules.insert("", tk.END, text=" " + proc_name, image=icon,
                                       values=(mode, freq_info, msi_display))

    def on_rule_tree_selected(self, event=None):
        selected = self.app.tree_rules.selection()
        if selected:
            item = self.app.tree_rules.item(selected[0])
            process_name = item['text'].strip()
            mode = item['values'][0]
            freq_val = str(item['values'][1])
            msi_profile = item['values'][2] if len(item['values']) > 2 else "默认配置"

            self.app.combo_process_input.set(process_name)
            self.app.combo_mode.set(mode)
            self.app.entry_freq_input.delete(0, tk.END)
            self.app.entry_min_freq.delete(0, tk.END)
            self.app.entry_max_freq.delete(0, tk.END)

            if mode == "定频模式":
                self.app.entry_freq_input.insert(0, freq_val)
            else:
                parts = freq_val.split("-")
                if len(parts) >= 2:
                    self.app.entry_min_freq.insert(0, parts[0].strip())
                    self.app.entry_max_freq.insert(0, parts[1].strip())
            self.app.combo_msi_profile.set(msi_profile)
            self.app.msi_ctrl.on_msi_profile_selected()

    def clear_input_fields(self):
        self.app.combo_process_input.set('')
        self.app.combo_mode.set("定频模式")
        self.app.entry_freq_input.delete(0, tk.END)
        self.app.entry_freq_input.insert(0, '2200')
        self.app.entry_min_freq.delete(0, tk.END)
        self.app.entry_max_freq.delete(0, tk.END)
        self.app.combo_msi_profile.set("默认配置")
        if self.app.msi_service:
            self.app.lbl_msi_info.config(text="")

    def add_or_update_rule(self):
        proc_name = self.app.combo_process_input.get().strip()
        mode = self.app.combo_mode.get().strip()
        freq_str = self.app.entry_freq_input.get().strip()
        min_str = self.app.entry_min_freq.get().strip()
        max_str = self.app.entry_max_freq.get().strip()

        if not proc_name:
            messagebox.showwarning("提示", "请输入目标程序名称")
            return

        freq, min_freq, max_freq = 2200, 200, 4000
        if mode == "定频模式":
            try:
                freq = int(freq_str)
                if freq <= 0 or freq > 4000: raise ValueError
            except ValueError:
                messagebox.showerror("错误", "频率必须为有效正整数 (1-4000 MHz)")
                return
        else:
            if not min_str and not max_str:
                messagebox.showerror("错误", "频段不能为空")
                return
            try:
                min_freq, max_freq = int(min_str), int(max_str)
                if min_freq <= 0 or max_freq <= 0 or min_freq > max_freq: raise ValueError
            except ValueError:
                messagebox.showerror("错误", "频率下限和上限不合法")
                return

        self.add_rule_direct(proc_name, mode, freq, min_freq, max_freq, self.app.combo_msi_profile.get())

    def add_rule_direct(self, proc_name, mode, freq, min_freq, max_freq, msi_profile="默认配置"):
        active_profile = self.app.combo_profiles.get().strip()
        if not active_profile: return
        if not proc_name.lower().endswith('.exe'): proc_name += '.exe'

        rules = self.config_mgr.get_profile_rules(active_profile)
        new_rule_data = {
            'process': proc_name, 'mode': mode, 'frequency': freq,
            'min_freq': min_freq, 'max_freq': max_freq,
            'msi_profile': msi_profile if msi_profile != "默认配置" else None
        }
        updated = False
        new_rules = []
        for rule in rules:
            if rule['process'].lower() == proc_name.lower():
                new_rules.append(new_rule_data)
                updated = True
            else:
                new_rules.append(rule)

        if not updated: new_rules.append(new_rule_data)
        self.config_mgr.save_profile_rules(active_profile, new_rules)
        self.load_tree_rules()
        self.app.log(f"已更新规则: {proc_name} -> {mode}")

    def delete_selected_rule(self):
        selected = self.app.tree_rules.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择要删除的规则")
            return
        active_profile = self.app.combo_profiles.get().strip()
        proc_name = self.app.tree_rules.item(selected[0])['text'].strip()

        rules = self.config_mgr.get_profile_rules(active_profile)
        self.config_mgr.save_profile_rules(active_profile,
                                           [r for r in rules if r['process'].lower() != proc_name.lower()])
        self.load_tree_rules()
        self.app.log(f"已删除规则: {proc_name}")

    def launch_selected_rule(self):
        selected = self.app.tree_rules.selection()
        if not selected:
            messagebox.showwarning("提示", "请先选择要运行的规则")
            return
        success, msg = AppLauncher.launch_app(self.app.tree_rules.item(selected[0])['text'].strip())
        if success:
            self.app.log(msg)
        else:
            messagebox.showerror("启动失败", msg)