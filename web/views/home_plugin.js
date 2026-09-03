const HomePlugin = {
  id: "home",
  title: "主页",
  order: 10,
  isNavItem: true,
  icon: `<svg viewBox="0 0 24 24"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>`,

  renderView() {
    return `
      <!-- 1. 顶部基础数据统计指标 -->
      <div class="stat-grid">
        <div class="stat-card">
          <svg viewBox="0 0 24 24"><path d="M4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm16-4H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H8V4h12v12z"/></svg>
          <div><div style="font-size:11px; color:var(--text-secondary);">总软件数</div><div id="stat-total-apps" class="stat-card-num">0</div></div>
        </div>
        <div class="stat-card">
          <svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
          <div><div style="font-size:11px; color:var(--text-secondary);">总打开次数</div><div id="stat-total-launches" class="stat-card-num">0 次</div></div>
        </div>
        <div class="stat-card">
          <svg viewBox="0 0 24 24"><path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z"/></svg>
          <div><div style="font-size:11px; color:var(--text-secondary);">长时间未使用</div><div id="stat-unused-count" class="stat-card-num" style="color:#EF4444;">0</div></div>
        </div>
        <div class="stat-card">
          <svg viewBox="0 0 24 24"><path d="M3 15h18v-2H3v2zm0 4h18v-2H3v2zm0-8h18V9H3v2zm0-6v2h18V5H3z"/></svg>
          <div><div style="font-size:11px; color:var(--text-secondary);">当前调度模式</div><div id="stat-dispatch-mode" class="stat-card-num" style="font-size:15px; color:var(--primary);">焦点模式</div></div>
        </div>
      </div>

      <!-- 2. 现代科技质感: 调度核心与硬件监测仪表盘 -->
      <div class="hardware-monitor-panel">
        <div class="hardware-panel-header">
          <div style="display:flex; align-items:center; gap:10px;">
            <div style="width:10px; height:10px; border-radius:50%; background:#10B981; box-shadow:0 0 8px #10B981;" id="home-pulse-dot"></div>
            <span style="font-weight:700; font-size:14px; letter-spacing:-0.2px;">调度核心与硬件监测</span>
            <span id="home-monitor-badge" class="badge-beta" style="background:#10B981; font-size:10px; padding:2px 7px;">监控运行中</span>
          </div>
          <div style="display:flex; gap:8px;">
            <button class="btn btn-outline" style="padding:4px 10px; font-size:11px; border-radius:6px;" onclick="App.toggleMonitor()" id="home-btn-toggle-monitor">切换监控</button>
            <button class="btn btn-outline" style="padding:4px 10px; font-size:11px; border-radius:6px;" onclick="HomePlugin.refreshHardwareInfo()">重新探测显卡</button>
          </div>
        </div>
        <div class="hardware-metrics-grid">
          <div class="hardware-metric-card">
            <div class="metric-label">
              <svg viewBox="0 0 24 24" style="width:14px; height:14px; fill:currentColor;"><path d="M4 6h16v12H4zM2 4v16h20V4H2zm4 4h4v4H6zm6 0h6v2h-6zm0 4h6v2h-6z"/></svg>
              <span>检测显卡设备</span>
            </div>
            <div id="home-gpu-name" class="metric-val">正在探测...</div>
          </div>
          <div class="hardware-metric-card">
            <div class="metric-label">
              <svg viewBox="0 0 24 24" style="width:14px; height:14px; fill:currentColor;"><path d="M12 2a10 10 0 1010 10A10 10 0 0012 2zm1 14.5h-2v-2h2zm0-4h-2V7h2z"/></svg>
              <span>时钟频率 (当前 / 锁定上限)</span>
            </div>
            <div id="home-gpu-freq" class="metric-val" style="color:var(--primary);">检测中...</div>
          </div>
          <div class="hardware-metric-card">
            <div class="metric-label">
              <svg viewBox="0 0 24 24" style="width:14px; height:14px; fill:currentColor;"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V5h14v14z"/></svg>
              <span>前台活动焦点目标</span>
            </div>
            <div id="home-active-focus" class="metric-val">等待检测...</div>
          </div>
        </div>
      </div>

      <!-- 3. 最近运行 Hero 展示卡片 -->
      <div id="hero-card" class="card" style="display:none; background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); color:#FFF; justify-content:space-between; align-items:center;">
        <div style="display:flex; gap:16px; align-items:center;">
          <img id="hero-icon" src="" style="width:60px; height:60px; border-radius:12px; background:#FFF; padding:4px;">
          <div>
            <div style="font-size:11px; color:#93C5FD; font-weight:600; margin-bottom:4px;">最近打开运行</div>
            <div id="hero-title" style="font-size:18px; font-weight:700;">软件名称</div>
            <div id="hero-sub" style="font-size:12px; color:#94A3B8; margin-top:4px;">上次运行: 刚刚</div>
          </div>
        </div>
        <div style="display:flex; gap:8px;">
          <button id="hero-launch-btn" class="btn" style="background:#3B82F6; padding:8px 16px; font-size:12px;">启动软件</button>
          <button id="hero-kill-btn" class="btn btn-danger" style="padding:8px 14px; font-size:12px;">关闭软件</button>
          <button id="hero-detail-btn" class="btn btn-outline" style="color:#FFF; border-color:#475569; padding:8px 14px; font-size:12px;">配置定制</button>
        </div>
      </div>

      <!-- 4. 实时调度与运行日志控制台 (常驻主页展示) -->
      <div class="card">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
          <div style="display:flex; align-items:center; gap:8px;">
            <span style="font-size:13px; font-weight:700;">实时调度与窗口焦点日志</span>
            <span style="font-size:11px; color:var(--text-secondary);">(焦点转移、调频与状态流转实时更新)</span>
          </div>
          <button class="btn btn-outline" style="padding:2px 8px; font-size:11px;" onclick="HomePlugin.clearLogs()">清空日志</button>
        </div>
        <div id="home-log-box" class="log-console" style="height:140px;">(正在加载实时调度日志...)</div>
      </div>

      <!-- 5. 常用软件网格 -->
      <div class="card">
        <div style="font-size:13px; font-weight:700; margin-bottom:12px;">最近打开的软件 (单击选中/再次取消，双击进入详情)</div>
        <div id="home-recent-grid" class="app-grid"></div>
      </div>
    `;
  },

  async onActivate() {
    const data = await window.pywebview.api.get_overview_data();
    document.getElementById('stat-total-apps').innerText = data.total_count;
    document.getElementById('stat-total-launches').innerText = data.total_launches + ' 次';
    document.getElementById('stat-unused-count').innerText = data.unused_count;

    const modeTxt = App.systemSettings.schedule_mode === 'queue' ? '排队器模式' : '焦点模式';
    document.getElementById('stat-dispatch-mode').innerText = modeTxt;

    if (data.monitor_status) {
      this.updateHardwareCard(data.monitor_status);
    }

    if (data.recent_app) {
      document.getElementById('hero-card').style.display = 'flex';
      document.getElementById('hero-icon').src = data.recent_app.icon;
      document.getElementById('hero-title').innerText = data.recent_app.name;
      document.getElementById('hero-sub').innerText = '上次运行: ' + data.recent_app.last_run_time;
      document.getElementById('hero-launch-btn').onclick = (e) => { e.stopPropagation(); window.pywebview.api.launch_app(data.recent_app.id); };
      document.getElementById('hero-kill-btn').onclick = (e) => { e.stopPropagation(); window.pywebview.api.terminate_app(data.recent_app.id); };
      document.getElementById('hero-detail-btn').onclick = (e) => { e.stopPropagation(); App.navTo('detail', { appId: data.recent_app.id, name: data.recent_app.name }); };
    }

    const grid = document.getElementById('home-recent-grid');
    grid.innerHTML = data.recent_list.map(a => LibraryPlugin.renderCard(a)).join('');

    const logs = await window.pywebview.api.get_logs();
    const hBox = document.getElementById('home-log-box');
    if (hBox && logs && logs.length > 0) {
      hBox.innerText = logs.join('\n');
      hBox.scrollTop = hBox.scrollHeight;
    }
  },

  updateHardwareCard(status) {
    if (!status) return;
    const badge = document.getElementById('home-monitor-badge');
    const dot = document.getElementById('home-pulse-dot');
    const btn = document.getElementById('home-btn-toggle-monitor');
    const gpuEl = document.getElementById('home-gpu-name');
    const freqEl = document.getElementById('home-gpu-freq');
    const focusEl = document.getElementById('home-active-focus');

    if (badge) {
      badge.innerText = status.monitoring ? (status.status_text || '监控运行中') : '监控已停止';
      badge.style.background = status.monitoring ? (status.status_color || '#10B981') : '#64748B';
    }
    if (dot) {
      dot.style.background = status.monitoring ? (status.status_color || '#10B981') : '#64748B';
      dot.style.boxShadow = status.monitoring ? `0 0 8px ${status.status_color || '#10B981'}` : 'none';
    }
    if (btn) {
      btn.innerText = status.monitoring ? '停止自动调度' : '启动自动调度';
    }
    if (gpuEl) {
      gpuEl.innerText = status.gpu_name || '未检测到独立显卡';
      gpuEl.style.color = status.gpu_available ? 'var(--text-primary)' : '#EF4444';
    }
    if (freqEl) {
      if (status.gpu_available) {
        const cur = status.current_freq ? `${status.current_freq} MHz` : '动态';
        const max = status.max_freq ? `${status.max_freq} MHz` : '默认';
        freqEl.innerText = `${cur} / 上限 ${max}`;
      } else {
        freqEl.innerText = '显卡未就绪 (已安全旁路)';
        freqEl.style.color = '#EF4444';
      }
    }
    if (focusEl) {
      let targetName = status.active_app;
      if (!targetName || targetName === "无") {
        targetName = '等待目标窗口激活';
      } else if (targetName === "Program Manager") {
        targetName = '前台保持 (查看主程序)';
      }
      focusEl.innerText = targetName;
    }
  },

  async refreshHardwareInfo() {
    await App.updateMonitorUI();
  },

  async clearLogs() {
    await window.pywebview.api.clear_logs();
    const boxes = [
      document.getElementById('home-log-box'),
      document.getElementById('global-log-box'),
      document.getElementById('detail-log-box')
    ];
    boxes.forEach(b => { if (b) b.innerText = ''; });
  }
};

App.registerPlugin(HomePlugin);
