/**
 * Nanako App Manager - 微内核框架核心
 */
const App = {
  plugins: {},
  routes: {},
  navHistory: [],
  singleSelectedAppId: null,
  selectedAppIds: new Set(),
  isMultiSelect: false,
  systemSettings: {},
  allPowerPlans: [],
  allMsiProfiles: [],
  logTimer: null,
  monitorStatus: {},
  isSidebarCollapsed: false,

  // 1. 注册插件接口
  registerPlugin(plugin) {
    if (!plugin.id) throw new Error("Plugin must provide an ID");
    this.plugins[plugin.id] = plugin;
  },

  // 2. 核心初始化
  async init() {
    const viewsSlot = document.getElementById("views-slot");
    const modalsSlot = document.getElementById("modals-slot");
    const sidebarNav = document.getElementById("sidebar-nav");

    const sortedPlugins = Object.values(this.plugins).sort((a, b) => (a.order || 100) - (b.order || 100));

    sortedPlugins.forEach(p => {
      if (p.isNavItem) {
        const navEl = document.createElement("div");
        navEl.className = "nav-item";
        navEl.id = `nav-item-${p.id}`;
        navEl.onclick = () => App.navTo(p.id);
        navEl.innerHTML = `${p.icon}<span>${p.title}</span>`;
        sidebarNav.appendChild(navEl);
      }

      if (p.renderView) {
        const viewEl = document.createElement("div");
        viewEl.className = "page-view";
        viewEl.id = `page-${p.id}`;
        viewEl.innerHTML = p.renderView();
        viewsSlot.appendChild(viewEl);
      }

      if (p.renderModal) {
        const modalContainer = document.createElement("div");
        modalContainer.innerHTML = p.renderModal();
        modalsSlot.appendChild(modalContainer);
      }

      if (typeof p.onInit === "function") {
        p.onInit(App);
      }
    });

    await this.loadGlobalSettings();
    await this.loadPowerPlans();
    await this.loadMsiProfiles();
    this.applyAppearanceSettings(this.systemSettings);
    await this.updateMonitorUI();
    this.startLogPolling();

    // 默认进入主页
    this.navTo("home", {}, false);
  },

  // 3. 统一路由管理器
  navTo(pageId, params = {}, pushHistory = true) {
    if (pushHistory) {
      this.navHistory.push({ page: pageId, params });
    } else {
      this.navHistory = [{ page: pageId, params }];
    }

    document.querySelectorAll(".page-view").forEach(el => el.classList.remove("active"));
    document.querySelectorAll(".nav-item").forEach(el => el.classList.remove("active"));

    const navItem = document.getElementById(`nav-item-${pageId}`);
    if (navItem) navItem.classList.add("active");

    const pageEl = document.getElementById(`page-${pageId}`);
    if (pageEl) pageEl.classList.add("active");

    this.updateBreadcrumbs(pageId, params);

    const activePlugin = this.plugins[pageId];
    if (activePlugin && typeof activePlugin.onActivate === "function") {
      activePlugin.onActivate(params);
    }
  },

  goBack() {
    if (this.navHistory.length > 1) {
      this.navHistory.pop();
      const prev = this.navHistory[this.navHistory.length - 1];
      this.navTo(prev.page, prev.params, false);
    } else {
      // 处于主页时点击返回按钮，刷新当前主页数据
      if (this.plugins['home'] && typeof this.plugins['home'].onActivate === 'function') {
        this.plugins['home'].onActivate();
      }
    }
  },

  toggleSidebar() {
    this.isSidebarCollapsed = !this.isSidebarCollapsed;
    document.body.classList.toggle('sidebar-collapsed', this.isSidebarCollapsed);
    if (window.pywebview && window.pywebview.api) {
      window.pywebview.api.save_sidebar_state(this.isSidebarCollapsed);
    }
  },

  sanitizeText(str) {
    if (!str) return "";
    return String(str)
      .replace(/[\uFFFD\u0000-\u001F\u007F-\u009F\u200B-\u200F\uFEFF]/g, '')
      .replace(/^[\s\u3000\u00A0]+|[\s\u3000\u00A0]+$/g, '')
      .replace(/[\s\u3000\u00A0]+/g, ' ');
  },

  escapeHtml(str) {
    if (!str) return "";
    return this.sanitizeText(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  },

  updateBreadcrumbs(pageId, params) {
    const bar = document.getElementById("breadcrumb-bar");
    if (!bar) return;
    const plugin = this.plugins[pageId];
    const title = plugin ? plugin.title : pageId;

    if (pageId === "home") {
      bar.innerHTML = '<span class="current">主页</span>';
    } else if (pageId === "detail") {
      const cleanName = this.escapeHtml(params.name || '应用详情');
      bar.innerHTML = `<span class="link" onclick="App.navTo('home')">主页</span> <span class="sep">/</span> <span class="link" onclick="App.navTo('library')">软件库</span> <span class="sep">/</span> <span class="current">${cleanName}</span>`;
    } else {
      bar.innerHTML = `<span class="link" onclick="App.navTo('home')">主页</span> <span class="sep">/</span> <span class="current">${this.escapeHtml(title)}</span>`;
    }
  },

  // 4. 外观、毛玻璃与自定义色彩动态应用核心 (全量实时响应)
  applyAppearanceSettings(s) {
    if (!s) return;
    const root = document.documentElement;
    const isDark = document.body.classList.contains('dark-mode');

    // 1. 透明度与模糊度数值计算
    const opacity = (s.ui_opacity !== undefined && s.ui_opacity !== null) ? Math.max(0.2, Math.min(1.0, parseFloat(s.ui_opacity))) : 0.88;
    const blurVal = (s.ui_blur !== undefined && s.ui_blur !== null) ? Math.max(0, Math.min(30, parseInt(s.ui_blur))) : 16;

    // 2. 动态生成各层级 RGBA 颜色，彻底杜绝 CSS 静态求值失效问题
    const cardRgb = isDark ? "30, 41, 59" : "255, 255, 255";
    const subCardRgb = isDark ? "51, 65, 85" : "239, 246, 255";
    const borderRgb = isDark ? "71, 85, 105" : "226, 232, 240";

    const cardGlass = `rgba(${cardRgb}, ${opacity})`;
    const sidebarGlass = `rgba(${cardRgb}, ${Math.min(1.0, opacity + 0.04)})`;
    const subContainerGlass = `rgba(${subCardRgb}, ${Math.max(0.2, opacity * 0.75)})`;
    const dynamicBorder = `rgba(${borderRgb}, ${Math.max(0.3, opacity * 0.9)})`;

    root.style.setProperty('--bg-card-glass', cardGlass);
    root.style.setProperty('--sidebar-bg', sidebarGlass);
    root.style.setProperty('--sidebar-active', subContainerGlass);
    root.style.setProperty('--border-color', dynamicBorder);
    root.style.setProperty('--ui-opacity', opacity);
    root.style.setProperty('--ui-blur', `${blurVal}px`);

    // 3. 自定义背景壁纸与极光层联动
    const wpLayer = document.getElementById('app-wallpaper-layer');
    if (s.custom_wallpaper && s.custom_wallpaper.trim()) {
      document.body.classList.add('has-custom-wallpaper');
      if (wpLayer) {
        wpLayer.style.backgroundImage = `url("${s.custom_wallpaper.trim()}")`;
        wpLayer.style.backgroundSize = s.custom_wallpaper_fit || 'cover';
      }
    } else {
      document.body.classList.remove('has-custom-wallpaper');
      if (wpLayer) wpLayer.style.backgroundImage = '';
    }

    // 4. 自定义主文字颜色
    if (s.custom_text_color && s.custom_text_color.trim()) {
      root.style.setProperty('--text-primary', s.custom_text_color.trim());
    } else {
      root.style.removeProperty('--text-primary');
    }

    // 5. 自定义主题强调主色
    if (s.custom_primary_color && s.custom_primary_color.trim()) {
      const pColor = s.custom_primary_color.trim();
      root.style.setProperty('--primary', pColor);
      root.style.setProperty('--primary-hover', pColor);
    } else {
      root.style.removeProperty('--primary');
      root.style.removeProperty('--primary-hover');
    }

    // 6. 边栏收起状态
    this.isSidebarCollapsed = (s.sidebar_collapsed === true);
    document.body.classList.toggle('sidebar-collapsed', this.isSidebarCollapsed);

    // 7. 同步实时预览视窗 (若当前在设置页)
    const previewGlass = document.getElementById('appearance-live-preview');
    if (previewGlass) {
      previewGlass.style.background = cardGlass;
      previewGlass.style.backdropFilter = `blur(${blurVal}px) saturate(160%)`;
      previewGlass.style.webkitBackdropFilter = `blur(${blurVal}px) saturate(160%)`;
      previewGlass.style.borderColor = dynamicBorder;
    }
  },

  // 5. 全局日志拉取与状态同步
  startLogPolling() {
    if (this.logTimer) clearInterval(this.logTimer);
    this.logTimer = setInterval(async () => {
      if (window.pywebview && window.pywebview.api) {
        if (this.systemSettings.enable_logging !== false) {
          try {
            const logs = await window.pywebview.api.get_logs();
            const str = (logs && logs.length > 0) ? logs.join('\n') : "(暂无日志记录)";
            const boxes = [
              document.getElementById('global-log-box'),
              document.getElementById('detail-log-box'),
              document.getElementById('home-log-box')
            ];
            boxes.forEach(box => {
              if (box) {
                const shouldScroll = box.scrollTop + box.clientHeight >= box.scrollHeight - 60;
                box.innerText = str;
                if (shouldScroll) {
                  box.scrollTop = box.scrollHeight;
                }
              }
            });
          } catch (e) {
            console.error("拉取日志失败:", e);
          }
        }
        await this.updateMonitorUI();
      }
    }, 1200);
  },

  async updateMonitorUI() {
    if (!window.pywebview || !window.pywebview.api) return;
    try {
      const status = await window.pywebview.api.get_monitor_status();
      if (!status) return;
      this.monitorStatus = status;

      // 1. 模式胶囊
      const modeBadge = document.getElementById('top-mode-badge');
      if (modeBadge) {
        modeBadge.innerText = (this.systemSettings.schedule_mode === 'queue') ? '排队模式' : '焦点模式';
      }

      // 2. 管理员胶囊
      const adminBadge = document.getElementById('top-admin-badge');
      const adminTxt = document.getElementById('txt-admin-status');
      if (adminBadge) {
        adminBadge.style.display = 'inline-flex';
        if (status.is_admin) {
          adminBadge.className = "capsule-badge capsule-admin";
          if (adminTxt) adminTxt.innerText = "管理员";
          adminBadge.title = "管理员权限已就绪 (硬件锁频与电源管理已激活)";
        } else {
          adminBadge.className = "capsule-badge capsule-admin warning";
          if (adminTxt) adminTxt.innerText = "未获管理员权限";
          adminBadge.title = "未获取管理员权限将导致显卡锁频失败！点击重启提权";
        }
      }

      // 3. 监控状态胶囊
      const monitorBadge = document.getElementById('top-monitor-badge');
      const monitorTxt = document.getElementById('txt-monitor-status');
      if (monitorBadge) {
        if (status.monitoring) {
          monitorBadge.className = "capsule-badge capsule-monitor";
          let label = "监控中";
          if (status.active_app && status.active_app !== "无" && status.active_app !== "Program Manager") {
            label = `当前: ${status.active_app}`;
          }
          if (monitorTxt) monitorTxt.innerText = label;
          monitorBadge.title = `核心监控运行中 · 目标应用: ${status.active_app || '等待中'} (点击切换暂停)`;
        } else {
          monitorBadge.className = "capsule-badge capsule-monitor stopped";
          if (monitorTxt) monitorTxt.innerText = "监控已暂停";
          monitorBadge.title = "监控核心已停止运行 (点击启动)";
        }
      }

      // 触发主页刷新动态硬件卡片
      if (this.plugins['home'] && typeof this.plugins['home'].updateHardwareCard === 'function') {
        this.plugins['home'].updateHardwareCard(status);
      }
    } catch (e) {
      console.error("更新监控状态异常:", e);
    }
  },

  async requestAdmin() {
    if (confirm("当前启动器需要管理员权限以调用底层接口锁定显卡频率。是否立即以管理员身份重启？")) {
      await window.pywebview.api.elevate_admin();
    }
  },

  async toggleMonitor() {
    if (!window.pywebview || !window.pywebview.api) return;
    const res = await window.pywebview.api.toggle_monitor();
    await this.updateMonitorUI();
    return res;
  },

  async loadGlobalSettings() {
    this.systemSettings = await window.pywebview.api.get_settings();
    this.applyAppearanceSettings(this.systemSettings);
  },

  async loadPowerPlans() {
    this.allPowerPlans = await window.pywebview.api.get_power_plans();
  },

  async loadMsiProfiles() {
    this.allMsiProfiles = await window.pywebview.api.get_msi_profiles();
  },

  // 6. 全局事件与操作
  handleGlobalClick(e) {
    if (!e.target.closest('.app-card') && !e.target.closest('#batch-bar') && !e.target.closest('.custom-popup-menu') && !e.target.closest('.modal-box') && !e.target.closest('.top-actions') && !e.target.closest('.btn')) {
      if (!this.isMultiSelect) {
        this.singleSelectedAppId = null;
        document.querySelectorAll('.app-card').forEach(c => c.classList.remove('selected'));
      }
    }
    document.querySelectorAll('.custom-popup-menu').forEach(m => m.style.display = 'none');
    const filter = document.getElementById('filter-dropdown');
    if (filter) filter.style.display = 'none';
  },

  toggleMultiSelectMode() {
    this.isMultiSelect = !this.isMultiSelect;
    document.body.classList.toggle('multi-select-active', this.isMultiSelect);
    document.getElementById('batch-bar').style.display = this.isMultiSelect ? 'flex' : 'none';
    document.getElementById('txt-multiselect').innerText = this.isMultiSelect ? '取消' : '多选';
    if (!this.isMultiSelect) {
      this.selectedAppIds.clear();
      if (this.plugins['library']) this.plugins['library'].refresh();
    }
  },

  async quickLaunchSelected() {
    if (!this.singleSelectedAppId) return alert("请先单击选中一个软件，或双击进入详情");
    await window.pywebview.api.launch_app(this.singleSelectedAppId);
  },

  async quickTerminateSelected() {
    if (!this.singleSelectedAppId) return alert("请先单击选择要关闭的软件");
    const res = await window.pywebview.api.terminate_app(this.singleSelectedAppId);
    alert(res.msg);
  },

  toggleTheme() {
    const isDark = document.body.classList.toggle('dark-mode');
    this.systemSettings.theme = isDark ? 'dark' : 'light';
    if (window.pywebview && window.pywebview.api) {
      window.pywebview.api.save_settings(this.systemSettings);
    }
  },

  onGlobalSearch() { if (this.plugins['library']) this.plugins['library'].refresh(); }
};

window.addEventListener('pywebviewready', () => App.init());
