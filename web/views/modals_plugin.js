const ModalsPlugin = {
  id: "modals",
  order: 99,
  isNavItem: false,
  contextAppId: null,
  contextApp: null,
  pendingFiles: [],

  renderModal() {
    return `
      <!-- 全屏捕获倒计时遮罩 -->
      <div id="capture-countdown-overlay">
        <div style="font-size:18px; font-weight:700; margin-bottom:12px;">请立即切换到目标窗口/游戏...</div>
        <div id="countdown-num" style="font-size:64px; font-weight:900; color:#3B82F6;">3</div>
        <div style="font-size:13px; color:#94A3B8; margin-top:8px;">倒计时结束后将自动捕获并添加至软件库</div>
      </div>

      <!-- 1. 应用卡片动态多级右键菜单 (Submenu) -->
      <div id="app-context-menu" class="custom-popup-menu" style="min-width:190px;">
        <div class="menu-item" onclick="ModalsPlugin.ctxLaunch()">
          <svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
          <span>启动软件</span>
        </div>
        <div class="menu-item" style="color:#EF4444;" onclick="ModalsPlugin.ctxKill()">
          <svg viewBox="0 0 24 24"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
          <span>关闭进程</span>
        </div>
        <div class="menu-divider"></div>
        <div class="menu-item" onclick="ModalsPlugin.ctxDetail()">
          <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/></svg>
          <span>应用详情与调优</span>
        </div>

        <!-- 二级子菜单: 加入分组 (支持多分组归属与跟随策略选择) -->
        <div class="menu-item has-submenu" id="ctx-submenu-add-group">
          <div style="display:flex; align-items:center; gap:10px;">
            <svg viewBox="0 0 24 24"><path d="M10 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z"/></svg>
            <span>加入新分组</span>
          </div>
          <span class="submenu-arrow">▶</span>
          <div class="submenu" id="ctx-add-group-list"></div>
        </div>

        <!-- 二级子菜单: 切换当前跟随的策略分组 -->
        <div class="menu-item has-submenu" id="ctx-submenu-follow-group">
          <div style="display:flex; align-items:center; gap:10px;">
            <svg viewBox="0 0 24 24"><path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"/></svg>
            <span>切换策略跟随组</span>
          </div>
          <span class="submenu-arrow">▶</span>
          <div class="submenu" id="ctx-follow-group-list"></div>
        </div>

        <!-- 二级子菜单: 从已有分组中移出 -->
        <div class="menu-item has-submenu" id="ctx-submenu-remove-group">
          <div style="display:flex; align-items:center; gap:10px;">
            <svg viewBox="0 0 24 24"><path d="M19 13H5v-2h14v2z"/></svg>
            <span>从分组中移出</span>
          </div>
          <span class="submenu-arrow">▶</span>
          <div class="submenu" id="ctx-remove-group-list"></div>
        </div>

        <div class="menu-divider"></div>
        <div class="menu-item" style="color:#EF4444;" onclick="ModalsPlugin.ctxDelete()">
          <svg viewBox="0 0 24 24"><path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg>
          <span>从库中删除应用</span>
        </div>
      </div>

      <!-- 2. 分组卡片专属右键菜单 -->
      <div id="group-context-menu" class="custom-popup-menu">
        <div class="menu-item" onclick="GroupsPlugin.ctxViewApps()">
          <svg viewBox="0 0 24 24"><path d="M4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm16-4H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H8V4h12v12z"/></svg>
          <span>查看组内所有应用</span>
        </div>
        <div class="menu-item" onclick="GroupsPlugin.ctxConfigPolicy()">
          <svg viewBox="0 0 24 24"><path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"/></svg>
          <span>配置分组统一调优策略...</span>
        </div>
        <div class="menu-item" onclick="GroupsPlugin.ctxSyncToApps()">
          <svg viewBox="0 0 24 24"><path d="M12 4V1L8 5l4 4V6c3.31 0 6 2.69 6 6 0 1.01-.25 1.97-.7 2.8l1.46 1.46A7.93 7.93 0 0 0 20 12c0-4.42-3.58-8-8-8zm0 14c-3.31 0-6-2.69-6-6 0-1.01.25-1.97.7-2.8L5.24 7.74A7.93 7.93 0 0 0 4 12c0 4.42 3.58 8 8 8v3l4-4-4-4v3z"/></svg>
          <span>同步策略至组内所有应用</span>
        </div>
        <div class="menu-item" onclick="GroupsPlugin.ctxRename()">
          <svg viewBox="0 0 24 24"><path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z"/></svg>
          <span>重命名该分组</span>
        </div>
        <div class="menu-divider"></div>
        <div class="menu-item" style="color:#EF4444;" onclick="GroupsPlugin.ctxDeleteGroup()">
          <svg viewBox="0 0 24 24"><path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg>
          <span>删除该分组 (移出所有应用)</span>
        </div>
      </div>

      <!-- 3. 添加软件模态框 -->
      <div id="modal-add" class="modal-overlay">
        <div class="modal-box">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
            <h3 style="font-size:15px; font-weight:700;">添加软件至库</h3>
            <button class="btn btn-outline" style="padding:2px 6px;" onclick="ModalsPlugin.close('modal-add')">✕</button>
          </div>
          <div class="form-row">
            <label>选择可执行程序 (.exe):</label>
            <div style="display:flex; gap:8px;">
              <input type="text" id="add-exe-path" class="input-text" placeholder="选择可执行程序文件或通过上方抓取前台" readonly>
              <button class="btn btn-outline" onclick="ModalsPlugin.browseFiles()">浏览文件...</button>
            </div>
          </div>
          <div class="form-row">
            <label>显示名称:</label>
            <input type="text" id="add-name" class="input-text">
          </div>
          <div class="form-row">
            <label>归属初始分组:</label>
            <select id="add-category" class="input-text"></select>
          </div>
          <div style="display:flex; justify-content:flex-end; gap:8px; margin-top:20px;">
            <button class="btn btn-outline" onclick="ModalsPlugin.close('modal-add')">取消</button>
            <button class="btn" onclick="ModalsPlugin.submitAdd()">确认添加</button>
          </div>
        </div>
      </div>

      <!-- 4. 分组统一调优策略模态框 -->
      <div id="modal-group-config" class="modal-overlay">
        <div class="modal-box">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
            <h3 style="font-size:15px; font-weight:700;" id="title-group-config">分组统一调优策略配置</h3>
            <button class="btn btn-outline" style="padding:2px 6px;" onclick="ModalsPlugin.close('modal-group-config')">✕</button>
          </div>
          <div style="font-size:12px; color:var(--text-secondary); margin-bottom:14px;">
            设置此分组的基准调控策略。当应用选择跟随该分组时，将实时套用此配置。
          </div>

          <div class="form-row">
            <label>组内统一 GPU 调频模式:</label>
            <select id="modal-group-gpu-mode" class="input-text" onchange="GroupsPlugin.onGroupModalModeChange()">
              <option value="不修改">不修改 (使用系统默认策略)</option>
              <option value="定频模式">定频锁定模式 (锁定目标频率)</option>
              <option value="频段模式">频段范围模式 (锁定最高/最低范围)</option>
            </select>
          </div>
          <div id="modal-group-fixed" class="form-row">
            <label>目标核心频率 (MHz):</label>
            <input type="number" id="modal-group-gpu-freq" class="input-text" value="2000">
          </div>
          <div id="modal-group-range" class="form-row" style="display:none; gap:10px;">
            <div style="flex:1;">
              <label>最低核心频率 (MHz):</label>
              <input type="number" id="modal-group-gpu-min" class="input-text" value="200">
            </div>
            <div style="flex:1;">
              <label>最高核心频率 (MHz):</label>
              <input type="number" id="modal-group-gpu-max" class="input-text" value="2400">
            </div>
          </div>
          <div class="form-row">
            <label>微星小飞机 (MSI Afterburner) 组联动预设:</label>
            <select id="modal-group-msi-profile" class="input-text"></select>
          </div>
          <div class="form-row">
            <label>组内统一专属电源计划:</label>
            <select id="modal-group-power-plan" class="input-text"></select>
          </div>

          <div style="display:flex; justify-content:space-between; align-items:center; margin-top:22px;">
            <button class="btn btn-outline" onclick="GroupsPlugin.submitSyncToApps()" title="将当前策略强制同步重置组内所有应用">一键同步至组内所有应用</button>
            <div style="display:flex; gap:8px;">
              <button class="btn btn-outline" onclick="ModalsPlugin.close('modal-group-config')">取消</button>
              <button class="btn" onclick="GroupsPlugin.submitGroupConfig()">保存分组策略</button>
            </div>
          </div>
        </div>
      </div>
    `;
  },

  // 打开应用右键多级菜单并动态装配子菜单项
  async openAppContextMenu(e, appId) {
    e.preventDefault();
    e.stopPropagation();
    this.contextAppId = appId;
    const app = await window.pywebview.api.get_app_detail(appId);
    if (!app) return;
    this.contextApp = app;

    const menu = document.getElementById('app-context-menu');
    menu.style.display = 'block';

    const menuW = 210;
    const menuH = 260;
    const clickX = e.clientX;
    const clickY = e.clientY;
    menu.style.left = Math.min(clickX, window.innerWidth - menuW) + 'px';
    menu.style.top = Math.min(clickY, window.innerHeight - menuH) + 'px';

    const allCats = await window.pywebview.api.get_categories();
    const validCats = allCats.filter(c => c !== '全部');
    const appCats = app.categories || [app.category || '常用工具'];
    const followGroup = app.follow_group || app.category || '常用工具';

    // 1. 装配“加入新分组”二级菜单
    const addSubmenu = document.getElementById('ctx-add-group-list');
    const unjoinedCats = validCats.filter(c => !appCats.includes(c));
    if (unjoinedCats.length === 0) {
      addSubmenu.innerHTML = '<div class="menu-item" style="color:var(--text-secondary); cursor:default;"><span>已加入所有分组</span></div>';
    } else {
      addSubmenu.innerHTML = unjoinedCats.map(c => `
        <div class="menu-item" onclick="ModalsPlugin.doAddToCategory('${c}')">
          <span>加入【${c}】并跟随其策略</span>
        </div>
      `).join('');
    }

    // 2. 装配“切换策略跟随组”二级菜单
    const followSubmenu = document.getElementById('ctx-follow-group-list');
    followSubmenu.innerHTML = `
      <div class="menu-item" style="${app.override_group_config ? 'color:var(--primary); font-weight:700;' : ''}" onclick="ModalsPlugin.doSetFollowGroup('独立定制')">
        <span>● 独立定制 (不跟随任何组)</span>
      </div>
      <div class="menu-divider"></div>
    ` + appCats.map(c => `
      <div class="menu-item" style="${(!app.override_group_config && followGroup === c) ? 'color:var(--primary); font-weight:700;' : ''}" onclick="ModalsPlugin.doSetFollowGroup('${c}')">
        <span>跟随【${c}】组策略</span>
      </div>
    `).join('');

    // 3. 装配“从分组中移出”二级菜单
    const removeSubmenu = document.getElementById('ctx-remove-group-list');
    if (appCats.length <= 1) {
      removeSubmenu.innerHTML = '<div class="menu-item" style="color:var(--text-secondary); cursor:default;"><span>仅剩一个默认归属，无法移出</span></div>';
    } else {
      removeSubmenu.innerHTML = appCats.map(c => `
        <div class="menu-item" style="color:#EF4444;" onclick="ModalsPlugin.doRemoveFromCategory('${c}')">
          <span>移出【${c}】</span>
        </div>
      `).join('');
    }

    // 防止二级子菜单向右展开时超出屏幕边界
    const submenus = menu.querySelectorAll('.submenu');
    const isRightOverflow = (clickX + menuW + 200 > window.innerWidth);
    submenus.forEach(sm => {
      sm.classList.toggle('open-left', isRightOverflow);
    });
  },

  // 快捷加入分组 (无弹窗，在日志中记录完成)
  async doAddToCategory(catName) {
    if (!this.contextAppId) return;
    await window.pywebview.api.add_app_to_category(this.contextAppId, catName, true);
    document.querySelectorAll('.custom-popup-menu').forEach(m => m.style.display = 'none');
    if (LibraryPlugin.refresh) LibraryPlugin.refresh();
  },

  // 切换策略跟随组 (无弹窗，在日志中记录完成)
  async doSetFollowGroup(groupName) {
    if (!this.contextAppId) return;
    await window.pywebview.api.set_app_follow_group(this.contextAppId, groupName);
    document.querySelectorAll('.custom-popup-menu').forEach(m => m.style.display = 'none');
    if (LibraryPlugin.refresh) LibraryPlugin.refresh();
  },

  // 从分组中移出 (无弹窗，在日志中记录完成)
  async doRemoveFromCategory(catName) {
    if (!this.contextAppId) return;
    await window.pywebview.api.remove_app_from_category(this.contextAppId, catName);
    document.querySelectorAll('.custom-popup-menu').forEach(m => m.style.display = 'none');
    if (LibraryPlugin.refresh) LibraryPlugin.refresh();
  },

  async ctxLaunch() { if (this.contextAppId) await window.pywebview.api.launch_app(this.contextAppId); },
  async ctxKill() { if (this.contextAppId) await window.pywebview.api.terminate_app(this.contextAppId); },
  async ctxDetail() { if (this.contextAppId) App.navTo('detail', { appId: this.contextAppId }); },

  async ctxDelete() {
    if (this.contextAppId && confirm('确定从软件库中移除该应用吗？')) {
      await window.pywebview.api.delete_app(this.contextAppId);
      if (LibraryPlugin.refresh) LibraryPlugin.refresh();
    }
  },

  async openAddModal() {
    this.pendingFiles = [];
    document.getElementById('add-exe-path').value = '';
    document.getElementById('add-name').value = '';
    const cats = await window.pywebview.api.get_categories();
    const sel = document.getElementById('add-category');
    sel.innerHTML = cats.filter(c => c !== '全部').map(c => `<option value="${c}">${c}</option>`).join('');
    document.getElementById('modal-add').style.display = 'flex';
  },

  close(id) { document.getElementById(id).style.display = 'none'; },

  async browseFiles() {
    const res = await window.pywebview.api.browse_executable_files();
    if (res && res.success && res.files && res.files.length > 0) {
      this.pendingFiles = res.files;
      document.getElementById('add-exe-path').value = res.files[0].exe_path;
      document.getElementById('add-name').value = res.files[0].name;
    }
  },

  async submitAdd() {
    if (this.pendingFiles.length === 0) return;
    const cat = document.getElementById('add-category').value;
    const name = document.getElementById('add-name').value.trim();

    await window.pywebview.api.save_app({
      name: name || this.pendingFiles[0].name,
      exe_path: this.pendingFiles[0].exe_path,
      exe_name: this.pendingFiles[0].exe_name,
      icon: this.pendingFiles[0].icon,
      category: cat,
      categories: [cat],
      follow_group: cat,
      override_group_config: false,
      gpu_mode: "不修改",
      gpu_freq: 2000,
      gpu_min_freq: 200,
      gpu_max_freq: 2400,
      power_plan_guid: "默认",
      msi_profile: "默认配置",
      proxy_url: "",
      auto_start: false
    });
    this.close('modal-add');
    if (LibraryPlugin.refresh) LibraryPlugin.refresh();
  },

  async captureForegroundDirect() {
    const res = await window.pywebview.api.capture_foreground_app(0);
    if (res && res.success && res.app) {
      if (confirm(`捕获到前台应用:\n${res.app.name}\n${res.app.exe_path}\n\n是否加入软件库？`)) {
        await window.pywebview.api.save_app({
          name: res.app.name,
          exe_path: res.app.exe_path,
          exe_name: res.app.exe_name,
          icon: res.app.icon,
          category: "常用工具",
          categories: ["常用工具"],
          follow_group: "常用工具",
          override_group_config: false,
          gpu_mode: "不修改",
          gpu_freq: 2000,
          gpu_min_freq: 200,
          gpu_max_freq: 2400,
          power_plan_guid: "默认",
          msi_profile: "默认配置",
          proxy_url: "",
          auto_start: false
        });
        if (LibraryPlugin.refresh) LibraryPlugin.refresh();
      }
    }
  }
};

App.registerPlugin(ModalsPlugin);
