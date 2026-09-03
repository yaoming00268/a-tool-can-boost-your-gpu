const StatsPlugin = {
  id: "stats",
  title: "统计",
  order: 60,
  isNavItem: true,
  icon: `<svg viewBox="0 0 24 24"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z"/></svg>`,

  renderView() {
    return `
      <div class="card">
        <h3 style="font-size:14px; font-weight:700; margin-bottom:12px;">启动打开频次排行榜 (Top Launches)</h3>
        <div id="stats-leaderboard"></div>
      </div>
      <div class="card">
        <h3 style="font-size:14px; font-weight:700; margin-bottom:12px; color:#EF4444;">长时间未使用应用预警清单</h3>
        <div id="stats-unused-list" class="app-grid"></div>
      </div>
    `;
  },

  async onActivate() {
    const sortedApps = await window.pywebview.api.get_apps("全部", "", "launch_count", "desc");
    const lb = document.getElementById('stats-leaderboard');
    lb.innerHTML = sortedApps.slice(0, 10).map((a, i) => `
      <div style="display:flex; justify-content:space-between; align-items:center; padding:10px 0; border-bottom:1px solid var(--border-color); cursor:pointer;" onclick="App.navTo('detail', { appId: '${a.id}', name: '${a.name.replace(/'/g, "\\'")}' })">
        <div style="display:flex; align-items:center; gap:12px;">
          <span style="font-weight:800; font-size:14px; width:24px; color:${i<3?'var(--primary)':'var(--text-secondary)'}">#${i+1}</span>
          <img src="${a.icon}" style="width:32px; height:32px; border-radius:6px;">
          <div>
            <div style="font-weight:700; font-size:13px;">${a.name}</div>
            <div style="font-size:11px; color:var(--text-secondary);">上次运行: ${a.last_run_time}</div>
          </div>
        </div>
        <div style="font-weight:700; font-size:14px; color:var(--primary);">${a.launch_count || 0} 次打开</div>
      </div>
    `).join('');

    const overview = await window.pywebview.api.get_overview_data();
    const unusedGrid = document.getElementById('stats-unused-list');
    unusedGrid.innerHTML = overview.unused_list.map(a => LibraryPlugin.renderCard(a)).join('');
  }
};

App.registerPlugin(StatsPlugin);
