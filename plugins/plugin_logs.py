from plugins.base_plugin import BasePlugin


class LogsPlugin(BasePlugin):
    plugin_id = "logs"
    plugin_name = "运行日志"
    slot = "bottom"
    order = 70

    def render_ui(self):
        return """
        <div class="card" style="margin-bottom:0;">
          <div class="card-title" style="margin-bottom:4px;">
            <span>运行实时日志</span>
            <button class="btn" style="padding:1px 6px; font-size:10px;" onclick="document.getElementById('log-box').innerHTML=''">清空</button>
          </div>
          <div id="log-box" style="height: 100px; overflow-y:auto; background:#0B0C0E; border:1px solid #232936; border-radius:4px; padding:6px; font-family:Consolas, monospace; font-size:11px; color:#A0AEC0;"></div>
        </div>
        """

    def render_js(self):
        return """
        window.appendSystemLog = function(msg) {
          const box = document.getElementById('log-box');
          if (!box) return;
          const time = new Date().toTimeString().split(' ')[0];
          const div = document.createElement('div');
          div.innerText = `[${time}] ${msg}`;
          box.appendChild(div);
          box.scrollTop = box.scrollHeight;
        };
        """
