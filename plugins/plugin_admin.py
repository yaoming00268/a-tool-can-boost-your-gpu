from plugins.base_plugin import BasePlugin
from core.gpu_service import is_admin, elevate_privileges


class AdminPlugin(BasePlugin):
    plugin_id = "admin"
    plugin_name = "权限与硬件状态"
    slot = "top"
    order = 10

    def get_api_methods(self):
        return {
            "check_status": self.check_status,
            "elevate": self.elevate
        }

    def check_status(self):
        msi = self.context.get("msi_service")
        msi_text = "[MSI 未安装]"
        msi_color = "#888"
        if msi and msi.is_installed():
            if msi.is_running():
                msi_text = "[MSI 已就绪]"
                msi_color = "#4CAF50"
            else:
                msi_text = "[MSI 未运行]"
                msi_color = "#FFA000"

        return {
            "is_admin": is_admin(),
            "msi_text": msi_text,
            "msi_color": msi_color
        }

    def elevate(self):
        success, msg = elevate_privileges()
        return {"success": success, "msg": msg}

    def render_ui(self):
        return """
        <div class="row" style="justify-content: space-between; padding: 4px 0; border-bottom: 1px solid #2B3240; margin-bottom: 10px;">
          <div style="display:flex; align-items:center; gap:8px;">
            <span id="admin-badge" style="font-weight: bold;">正在检测权限...</span>
            <button id="btn-elevate" class="btn btn-danger" style="display:none; padding: 2px 8px; font-size: 11px;" onclick="requestAdmin()">获取管理员权限</button>
          </div>
          <div id="msi-status-badge" style="font-weight: 500; color: #888;">微星小飞机检测中...</div>
        </div>
        """

    def render_js(self):
        return """
        async function refreshAdminStatus() {
          const res = await callApi('admin', 'check_status');
          if (res && res.success) {
            const badge = document.getElementById('admin-badge');
            const btn = document.getElementById('btn-elevate');
            if (res.data.is_admin) {
              badge.innerText = "● 管理员权限已就绪";
              badge.style.color = "#76B900";
              btn.style.display = "none";
            } else {
              badge.innerText = "● 警告: 未获取管理员权限 (锁频将不可用)";
              badge.style.color = "#FF5252";
              btn.style.display = "inline-block";
            }
            const msiBadge = document.getElementById('msi-status-badge');
            msiBadge.innerText = res.data.msi_text;
            msiBadge.style.color = res.data.msi_color;
          }
        }
        async function requestAdmin() {
          await callApi('admin', 'elevate');
        }
        window.addEventListener('pywebviewready', refreshAdminStatus);
        """
