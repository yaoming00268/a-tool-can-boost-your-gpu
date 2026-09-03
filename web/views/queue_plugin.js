const QueuePlugin = {
  id: "queue",
  title: "排队器",
  order: 30,
  isNavItem: true,
  icon: `<svg viewBox="0 0 24 24"><path d="M3 15h18v-2H3v2zm0 4h18v-2H3v2zm0-8h18V9H3v2zm0-6v2h18V5H3z"/></svg>`,
  queueApps: [],

  renderView() {
    return `
      <div class="card" style="margin-bottom:16px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <div>
            <h2 style="font-size:16px; font-weight:700; color:var(--text-primary);">排队器优先级调度面板</h2>
            <div style="font-size:12px; color:var(--text-secondary); margin-top:4px;">
              调度器在【排队器模式】下将从上至下依次检测；排在前面的应用优先执行调频和电源策略，未打开的应用自动跳过。
            </div>
          </div>
          <button class="btn" id="btn-save-queue-order" onclick="QueuePlugin.saveQueueOrderSubmit()">
            <svg viewBox="0 0 24 24"><path d="M17 3H5c-1.11 0-2 .9-2 2v14c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V7l-4-4zm-5 16c-1.66 0-3-1.34-3-3s1.34-3 3-3 3 1.34 3 3-1.34 3-3 3zm3-10H5V5h10v4z"/></svg>
            <span>保存排队顺序</span>
          </button>
        </div>
      </div>
      <div id="queue-list-container"></div>
    `;
  },

  async onActivate() {
    this.queueApps = await window.pywebview.api.get_queue_apps();
    this.renderQueueList();
  },

  renderQueueList() {
    const c = document.getElementById('queue-list-container');
    if (this.queueApps.length === 0) {
      c.innerHTML = '<div class="card" style="text-align:center; color:var(--text-secondary); padding:32px;">暂无应用，请先添加应用至软件库。</div>';
      return;
    }

    c.innerHTML = this.queueApps.map((a, idx) => {
      const runningBadge = a.is_running
        ? '<span class="queue-badge-running">● 运行中 (当前生效候选)</span>'
        : '<span class="queue-badge-stopped">未运行 (跳过)</span>';
      const effectiveGpu = a.effective_tuning ? a.effective_tuning.gpu_mode : '默认策略';

      return `
        <div class="queue-item">
          <div style="display:flex; align-items:center; gap:14px;">
            <div class="queue-rank">#${idx + 1}</div>
            <img src="${a.icon}" style="width:36px; height:36px; border-radius:8px;">
            <div>
              <div style="display:flex; align-items:center; gap:8px;">
                <span style="font-weight:700; font-size:13px;">${a.name}</span>
                ${runningBadge}
              </div>
              <div style="font-size:11px; color:var(--text-secondary); margin-top:2px;">
                进程: ${a.exe_name || a.exe_path} · 策略: ${effectiveGpu} · 分类: ${a.category}
              </div>
            </div>
          </div>
          <div style="display:flex; gap:6px; align-items:center;">
            <button class="btn-move" onclick="QueuePlugin.move(${idx}, -999)" title="置顶">▲ 置顶</button>
            <button class="btn-move" onclick="QueuePlugin.move(${idx}, -1)" title="上移">▲ 上移</button>
            <button class="btn-move" onclick="QueuePlugin.move(${idx}, 1)" title="下移">▼ 下移</button>
            <button class="btn-move" onclick="QueuePlugin.move(${idx}, 999)" title="置底">▼ 置底</button>
          </div>
        </div>
      `;
    }).join('');
  },

  move(index, offset) {
    if (offset === -999) {
      const item = this.queueApps.splice(index, 1)[0];
      this.queueApps.unshift(item);
    } else if (offset === 999) {
      const item = this.queueApps.splice(index, 1)[0];
      this.queueApps.push(item);
    } else {
      const targetIndex = index + offset;
      if (targetIndex < 0 || targetIndex >= this.queueApps.length) return;
      const temp = this.queueApps[index];
      this.queueApps[index] = this.queueApps[targetIndex];
      this.queueApps[targetIndex] = temp;
    }
    this.renderQueueList();
  },

  async saveQueueOrderSubmit() {
    const orderIds = this.queueApps.map(a => a.id);
    await window.pywebview.api.save_queue_order(orderIds);
    const btn = document.getElementById('btn-save-queue-order');
    if (btn) {
      const orig = btn.innerHTML;
      btn.innerHTML = '<span>● 排队顺序已保存</span>';
      setTimeout(() => { btn.innerHTML = orig; }, 2000);
    }
    // 顺序已保存并自动记录在运行日志中
  }
};

App.registerPlugin(QueuePlugin);
