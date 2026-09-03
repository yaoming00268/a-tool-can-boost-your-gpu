const DetailPlugin = {
  id: "detail",
  title: "详情与调优",
  order: 50,
  isNavItem: false,
  currentAppId: null,
  currentApp: null,

  renderView() {
    return `
      <!-- 1. 顶部应用摘要卡片 -->
      <div class="card" style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
        <div style="display:flex; gap:16px; align-items:center;">
          <div class="detail-icon-wrapper" onclick="DetailPlugin.triggerChangeIcon()" title="点击更换图标" style="cursor:pointer;">
            <img id="detail-icon" src="" style="width:56px; height:56px; border-radius:12px;">
          </div>
          <div>
            <div style="display:flex; align-items:center; gap:8px;">
              <h2 id="detail-name" style="font-size:18px; font-weight:700;">应用详情</h2>
              <div id="detail-categories-badges" style="display:flex; gap:5px; flex-wrap:wrap;"></div>
            </div>
            <div id="detail-path" style="font-size:12px; color:var(--text-secondary); margin-top:4px; max-width:550px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">路径: ...</div>
          </div>
        </div>
        <div style="display:flex; gap:8px; flex-shrink:0;">
          <button class="btn" onclick="DetailPlugin.launch()">启动软件</button>
          <button class="btn btn-danger" onclick="DetailPlugin.terminate()">关闭进程</button>
          <button class="btn btn-outline" onclick="DetailPlugin.openDir()">打开目录</button>
          <button class="btn btn-danger" onclick="DetailPlugin.deleteApp()">删除</button>
        </div>
      </div>

      <!-- 2. 选项卡导航 -->
      <div class="tab-nav">
        <div class="tab-btn active" onclick="DetailPlugin.switchTab('tuning')">硬件调优与电源定制</div>
        <div class="tab-btn" onclick="DetailPlugin.switchTab('stats')">打开频次与状态</div>
        <div class="tab-btn" onclick="DetailPlugin.switchTab('info')">基础信息与代理</div>
      </div>

      <!-- 选项卡 1: 硬件调优与电源定制 (含组策略选择下拉表) -->
      <div id="detail-tab-tuning" class="card">
        <!-- 组策略选择下拉表控制卡 (无弹窗，随时自由切换跟随策略) -->
        <div class="form-row" style="background:var(--sidebar-active); padding:14px; border-radius:12px; border:1px solid var(--border-color); margin-bottom:16px;">
          <label style="font-size:13px; font-weight:700; color:var(--text-primary); margin-bottom:6px;">策略继承与跟随模式选择 (下拉表):</label>
          <select id="tune-follow-group-select" class="input-text" style="margin-bottom:8px;" onchange="DetailPlugin.onFollowGroupSelectChange()"></select>
          <div id="txt-group-policy-hint" style="font-size:11px; color:var(--text-secondary);">
            * 可在上方下拉表中任意切换跟随已加入的分组配置或选择独立定制。切换后将自动无弹窗静默同步并记录至日志。
          </div>
        </div>

        <div class="form-row">
          <label>GPU 调频模式:</label>
          <select id="tune-gpu-mode" onchange="DetailPlugin.onGpuModeChange()">
            <option value="不修改">不修改 (使用系统默认策略)</option>
            <option value="定频模式">定频锁定模式 (锁定目标频率)</option>
            <option value="频段模式">频段范围模式 (锁定最高/最低范围)</option>
          </select>
        </div>
        <div id="tune-gpu-fixed" class="form-row">
          <label>目标核心频率 (MHz):</label>
          <input type="number" id="tune-gpu-freq" class="input-text" value="2000">
        </div>
        <div id="tune-gpu-range" class="form-row" style="display:none; gap:10px;">
          <div style="flex:1;">
            <label>最低核心频率 (MHz):</label>
            <input type="number" id="tune-gpu-min" class="input-text" value="200">
          </div>
          <div style="flex:1;">
            <label>最高核心频率 (MHz):</label>
            <input type="number" id="tune-gpu-max" class="input-text" value="2400">
          </div>
        </div>
        <div class="form-row">
          <label>微星小飞机 (MSI Afterburner) 预设联动:</label>
          <select id="tune-msi-profile" class="input-text"></select>
        </div>
        <div class="form-row">
          <label>专属电源计划联动:</label>
          <select id="tune-power-plan" class="input-text"></select>
        </div>
        
        <div style="display:flex; align-items:center; gap:12px; margin-top:12px;">
          <button class="btn" onclick="DetailPlugin.saveTuning()">保存调优方案</button>
          <span id="txt-tuning-save-feedback" style="font-size:12px; color:var(--success); font-weight:600; display:none;">● 已保存并即刻生效 (详情见日志)</span>
        </div>
      </div>

      <!-- 选项卡 2: 打开频次与状态 -->
      <div id="detail-tab-stats" class="card" style="display:none;">
        <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:14px; margin-bottom:16px;">
          <div class="stat-card"><div><div style="font-size:11px; color:var(--text-secondary);">累计打开次数</div><div id="detail-launch-count" class="stat-card-num">0 次</div></div></div>
          <div class="stat-card"><div><div style="font-size:11px; color:var(--text-secondary);">最近打开时间</div><div id="detail-last-run" style="font-size:14px; font-weight:700; margin-top:4px;">从未运行</div></div></div>
          <div class="stat-card"><div><div style="font-size:11px; color:var(--text-secondary);">活跃状态评估</div><div id="detail-active-status" style="font-size:14px; font-weight:700; margin-top:4px;">正常</div></div></div>
        </div>
        <div id="detail-log-box" class="log-console"></div>
      </div>

      <!-- 选项卡 3: 基础信息、多分组加入、开机自启、路径定位与代理 -->
      <div id="detail-tab-info" class="card" style="display:none;">
        <div class="form-row">
          <label>软件显示名称:</label>
          <input type="text" id="info-name" class="input-text">
        </div>
        <div class="form-row">
          <label>可执行文件名 (.exe):</label>
          <input type="text" id="info-exe" class="input-text">
        </div>
        <div class="form-row">
          <label>安装路径:</label>
          <div style="display:flex; gap:8px;">
            <input type="text" id="info-path" class="input-text" style="flex:1;">
            <button class="btn btn-outline" onclick="DetailPlugin.openDir()" title="在 Windows 资源管理器中打开并定位所在文件夹" style="padding:6px 12px; gap:6px; flex-shrink:0;">
              <svg viewBox="0 0 24 24" style="width:16px; height:16px; fill:currentColor;"><path d="M20 6h-8l-2-2H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm0 12H4V8h16v10z"/></svg>
              <span>定位文件夹</span>
            </button>
          </div>
        </div>

        <!-- 所在分组 (支持加入多个分组) -->
        <div class="form-row" style="background:var(--sidebar-active); padding:12px 14px; border-radius:10px; border:1px solid var(--border-color); margin-bottom:14px;">
          <label style="font-size:12px; font-weight:600; color:var(--text-primary); margin-bottom:8px;">加入的分组 (支持归入多个分组):</label>
          <div id="info-categories-checkboxes" style="display:flex; gap:12px; flex-wrap:wrap;"></div>
        </div>

        <!-- 开机自启选项 -->
        <div class="form-row" style="background:var(--sidebar-active); padding:12px 14px; border-radius:10px; border:1px solid var(--border-color); margin-bottom:14px;">
          <label style="display:flex; align-items:center; justify-content:space-between; cursor:pointer; margin:0;">
            <div>
              <div style="font-size:13px; font-weight:600; color:var(--text-primary);">随开机自动启动该应用</div>
              <div style="font-size:11px; color:var(--text-secondary); margin-top:2px;">开启后，系统登录时自动在后台启动此程序</div>
            </div>
            <input type="checkbox" id="info-auto-start" style="width:18px; height:18px; accent-color:var(--primary);">
          </label>
        </div>

        <div class="form-row">
          <label>专属网络代理地址 (留空使用全局/系统代理):</label>
          <input type="text" id="info-proxy-url" class="proxy-input-pill" placeholder="例如: http://127.0.0.1:7890">
        </div>

        <div style="display:flex; align-items:center; gap:12px; margin-top:12px;">
          <button class="btn" onclick="DetailPlugin.saveInfo()">保存应用配置</button>
          <span id="txt-info-save-feedback" style="font-size:12px; color:var(--success); font-weight:600; display:none;">● 配置已保存 (详见日志)</span>
        </div>
      </div>
    `;
  },

  async onActivate(params) {
    this.currentAppId = params.appId;
    const app = await window.pywebview.api.get_app_detail(params.appId);
    if (!app) return;
    this.currentApp = app;

    document.getElementById('detail-icon').src = app.icon;
    document.getElementById('detail-name').innerText = app.name;
    document.getElementById('detail-path').innerText = '路径: ' + (app.exe_path || app.exe_name);

    // 渲染多分组徽章
    const appCats = app.categories || [app.category || '常用工具'];
    const badgeContainer = document.getElementById('detail-categories-badges');
    badgeContainer.innerHTML = appCats.map(c => `<span class="app-chip" style="margin-top:0;">${c}</span>`).join('');

    // 填充调频表单
    document.getElementById('tune-gpu-mode').value = app.gpu_mode || '不修改';
    document.getElementById('tune-gpu-freq').value = app.gpu_freq || 2000;
    document.getElementById('tune-gpu-min').value = app.gpu_min_freq || 200;
    document.getElementById('tune-gpu-max').value = app.gpu_max_freq || 2400;
    this.onGpuModeChange();

    // 填充电源计划与 MSI
    const pSelect = document.getElementById('tune-power-plan');
    pSelect.innerHTML = '<option value="默认">跟随系统当前计划</option>' + App.allPowerPlans.map(p => `<option value="${p.guid}" ${p.guid === app.power_plan_guid ? 'selected' : ''}>${p.name}</option>`).join('');

    const mSelect = document.getElementById('tune-msi-profile');
    mSelect.innerHTML = '<option value="默认配置">默认配置</option>' + App.allMsiProfiles.map(p => `<option value="${p}" ${p === app.msi_profile ? 'selected' : ''}>${p}</option>`).join('');

    // 装配组策略选择下拉表 (在应用详情页可以再次更改组策略选择)
    await this.renderFollowGroupSelect();

    // 统计数据
    document.getElementById('detail-launch-count').innerText = `${app.launch_count || 0} 次`;
    document.getElementById('detail-last-run').innerText = app.last_run_time || '从未运行';
    document.getElementById('detail-active-status').innerText = app.is_unused ? '长时间未使用' : '活跃使用中';

    // 基础信息
    document.getElementById('info-name').value = app.name;
    document.getElementById('info-exe').value = app.exe_name;
    document.getElementById('info-path').value = app.exe_path || '';
    document.getElementById('info-proxy-url').value = app.proxy_url || '';
    document.getElementById('info-auto-start').checked = !!app.auto_start;

    // 装配多分组加入勾选框
    await this.renderCategoriesCheckboxes();
  },

  // 装配组策略选择下拉表
  async renderFollowGroupSelect() {
    const app = this.currentApp;
    if (!app) return;
    const select = document.getElementById('tune-follow-group-select');
    const appCats = app.categories || [app.category || '常用工具'];
    const followGroup = app.follow_group || app.category || '常用工具';
    const isOverride = (app.override_group_config === true || followGroup === '独立定制');

    let optionsHtml = `<option value="独立定制" ${isOverride ? 'selected' : ''}>独立定制 (不跟随任何分组配置，使用专属调控)</option>`;
    appCats.forEach(c => {
      const isSelected = (!isOverride && followGroup === c);
      optionsHtml += `<option value="${c}" ${isSelected ? 'selected' : ''}>跟随【${c}】分组统一调优策略</option>`;
    });

    select.innerHTML = optionsHtml;
    this.updatePolicyHint(isOverride ? '独立定制' : followGroup);
  },

  updatePolicyHint(selectedVal) {
    const hint = document.getElementById('txt-group-policy-hint');
    if (selectedVal === '独立定制') {
      hint.innerHTML = `<span style="color:#10B981; font-weight:600;">● 当前模式: 独立定制</span> (此软件对频率和电源的修改将专属于本应用，不随任何分组变动)`;
    } else {
      hint.innerHTML = `<span style="color:var(--primary); font-weight:600;">● 当前模式: 跟随【${selectedVal}】分组策略</span> (组内策略变动或同步时，此应用将自动继承更新)`;
    }
  },

  // 下拉表切换组策略选择 (无弹窗，在日志中记录完成)
  async onFollowGroupSelectChange() {
    const select = document.getElementById('tune-follow-group-select');
    const val = select.value;
    const app = this.currentApp;
    if (!app) return;

    if (val === '独立定制') {
      app.override_group_config = true;
      app.follow_group = '独立定制';
      await window.pywebview.api.set_app_follow_group(app.id, '独立定制');
    } else {
      app.override_group_config = false;
      app.follow_group = val;
      // 读取目标分组的配置并填充到表单
      const gCfg = await window.pywebview.api.get_group_config(val);
      document.getElementById('tune-gpu-mode').value = gCfg.gpu_mode || '不修改';
      document.getElementById('tune-gpu-freq').value = gCfg.gpu_freq || 2000;
      document.getElementById('tune-gpu-min').value = gCfg.gpu_min_freq || 200;
      document.getElementById('tune-gpu-max').value = gCfg.gpu_max_freq || 2400;
      document.getElementById('tune-power-plan').value = gCfg.power_plan_guid || '默认';
      document.getElementById('tune-msi-profile').value = gCfg.msi_profile || '默认配置';
      this.onGpuModeChange();

      app.gpu_mode = gCfg.gpu_mode || '不修改';
      app.gpu_freq = gCfg.gpu_freq || 2000;
      app.gpu_min_freq = gCfg.gpu_min_freq || 200;
      app.gpu_max_freq = gCfg.gpu_max_freq || 2400;
      app.power_plan_guid = gCfg.power_plan_guid || '默认';
      app.msi_profile = gCfg.msi_profile || '默认配置';

      await window.pywebview.api.set_app_follow_group(app.id, val);
      await window.pywebview.api.save_app(app);
    }

    this.updatePolicyHint(val);
    this.showFeedback('txt-tuning-save-feedback', `策略已切换为: ${val}`);
  },

  // 基础信息页多分组加入复选框
  async renderCategoriesCheckboxes() {
    const app = this.currentApp;
    if (!app) return;
    const allCats = await window.pywebview.api.get_categories();
    const validCats = allCats.filter(c => c !== '全部');
    const appCats = app.categories || [app.category || '常用工具'];
    const container = document.getElementById('info-categories-checkboxes');

    container.innerHTML = validCats.map(c => `
      <label style="display:flex; align-items:center; gap:6px; cursor:pointer; font-size:12px;">
        <input type="checkbox" class="cat-checkbox" value="${c}" ${appCats.includes(c) ? 'checked' : ''} onchange="DetailPlugin.onCategoryCheckboxChange('${c}', this.checked)">
        <span>${c}</span>
      </label>
    `).join('');
  },

  async onCategoryCheckboxChange(catName, isChecked) {
    const app = this.currentApp;
    if (!app) return;
    if (isChecked) {
      await window.pywebview.api.add_app_to_category(app.id, catName, false);
    } else {
      await window.pywebview.api.remove_app_from_category(app.id, catName);
    }
    // 重新拉取并更新
    const updated = await window.pywebview.api.get_app_detail(app.id);
    this.currentApp = updated;
    const badgeContainer = document.getElementById('detail-categories-badges');
    badgeContainer.innerHTML = (updated.categories || []).map(c => `<span class="app-chip" style="margin-top:0;">${c}</span>`).join('');
    await this.renderFollowGroupSelect();
  },

  switchTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    event.currentTarget.classList.add('active');
    document.getElementById('detail-tab-tuning').style.display = tab === 'tuning' ? 'block' : 'none';
    document.getElementById('detail-tab-stats').style.display = tab === 'stats' ? 'block' : 'none';
    document.getElementById('detail-tab-info').style.display = tab === 'info' ? 'block' : 'none';
  },

  onGpuModeChange() {
    const mode = document.getElementById('tune-gpu-mode').value;
    document.getElementById('tune-gpu-fixed').style.display = (mode === '定频模式') ? 'block' : 'none';
    document.getElementById('tune-gpu-range').style.display = (mode === '频段模式') ? 'flex' : 'none';
  },

  showFeedback(elId, text) {
    const el = document.getElementById(elId);
    if (el) {
      el.innerText = `● ${text}`;
      el.style.display = 'inline';
      setTimeout(() => { el.style.display = 'none'; }, 2600);
    }
  },

  // 保存调优方案 (无弹窗，在日志中记录完成)
  async saveTuning() {
    const app = await window.pywebview.api.get_app_detail(this.currentAppId);
    const mode = document.getElementById('tune-gpu-mode').value;
    const freq = parseInt(document.getElementById('tune-gpu-freq').value) || 2000;
    const minF = parseInt(document.getElementById('tune-gpu-min').value) || 200;
    const maxF = parseInt(document.getElementById('tune-gpu-max').value) || 2400;

    app.gpu_mode = mode;
    app.gpu_freq = freq;
    app.gpu_min_freq = minF;
    app.gpu_max_freq = maxF;
    app.power_plan_guid = document.getElementById('tune-power-plan').value;
    app.msi_profile = document.getElementById('tune-msi-profile').value;
    app.override_group_config = true;
    app.follow_group = "独立定制";

    await window.pywebview.api.save_app(app);
    this.currentApp = app;
    await this.renderFollowGroupSelect();
    this.showFeedback('txt-tuning-save-feedback', '专属调优方案已保存生效 (详见日志)');
  },

  // 保存基础信息 (无弹窗，在日志中记录完成)
  async saveInfo() {
    const app = await window.pywebview.api.get_app_detail(this.currentAppId);
    app.name = document.getElementById('info-name').value.trim();
    app.exe_name = document.getElementById('info-exe').value.trim();
    app.exe_path = document.getElementById('info-path').value.trim();
    app.proxy_url = document.getElementById('info-proxy-url').value.trim();
    app.auto_start = document.getElementById('info-auto-start').checked;

    await window.pywebview.api.save_app(app);
    this.currentApp = app;
    document.getElementById('detail-name').innerText = app.name;
    document.getElementById('detail-path').innerText = '路径: ' + (app.exe_path || app.exe_name);
    this.showFeedback('txt-info-save-feedback', '应用基础信息与自启动配置已保存 (详见日志)');
  },

  async launch() { await window.pywebview.api.launch_app(this.currentAppId); },
  async terminate() { await window.pywebview.api.terminate_app(this.currentAppId); },
  async openDir() { await window.pywebview.api.open_app_directory(this.currentAppId); },
  async deleteApp() {
    if (confirm('确定从软件库中移除该应用吗？')) {
      await window.pywebview.api.delete_app(this.currentAppId);
      App.goBack();
    }
  },
  async triggerChangeIcon() {
    const res = await window.pywebview.api.browse_custom_icon_file(this.currentAppId);
    if (res && res.success) document.getElementById('detail-icon').src = res.icon;
  }
};

App.registerPlugin(DetailPlugin);
