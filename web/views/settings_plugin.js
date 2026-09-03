const SettingsPlugin = {
  id: "settings",
  title: "设置",
  order: 70,
  isNavItem: true,
  icon: `<svg viewBox="0 0 24 24"><path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"/></svg>`,

  renderView() {
    return `
      <!-- 1. 个性化外观、自定义壁纸与玻璃拟态样式定制 -->
      <div class="card">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
          <div>
            <h3 style="font-size:15px; font-weight:700;">个性化外观与玻璃样式定制</h3>
            <div style="font-size:11px; color:var(--text-secondary); margin-top:2px;">支持自定义背景壁纸、文字色彩、UI组件透明度与毛玻璃景深效果，参数均持久化保存在配置文件中</div>
          </div>
          <button class="btn btn-outline" style="font-size:11px; padding:3px 10px;" onclick="SettingsPlugin.resetAppearance()">恢复默认外观</button>
        </div>

        <!-- 自定义壁纸 -->
        <div class="form-row" style="background:var(--sidebar-active); padding:14px; border-radius:12px; border:1px solid var(--border-color); margin-bottom:14px;">
          <label style="font-size:13px; font-weight:700; color:var(--text-primary); margin-bottom:8px;">背景壁纸定制:</label>
          <div style="display:flex; gap:14px; align-items:center;">
            <div id="wallpaper-preview-box" style="width:120px; height:68px; border-radius:8px; border:1px dashed var(--border-color); background:#0F172A; display:flex; align-items:center; justify-content:center; overflow:hidden; background-size:cover; background-position:center;">
              <span id="txt-wallpaper-hint" style="font-size:10px; color:#94A3B8;">无自定义壁纸</span>
            </div>
            <div style="flex:1; display:flex; flex-direction:column; gap:8px;">
              <div style="display:flex; gap:8px;">
                <button class="btn btn-outline" onclick="SettingsPlugin.chooseWallpaper()">选择本地图片壁纸...</button>
                <button class="btn btn-outline" style="color:#EF4444;" onclick="SettingsPlugin.removeWallpaper()">清除壁纸</button>
              </div>
              <div style="font-size:11px; color:var(--text-secondary);">支持 JPG, PNG, WEBP, BMP 等图片，高分辨率壁纸将自动适配视口。</div>
            </div>
          </div>
        </div>

        <!-- 自定义字体与主题色彩 -->
        <div style="display:grid; grid-template-columns:repeat(2, 1fr); gap:14px; margin-bottom:14px;">
          <div style="background:var(--sidebar-active); padding:12px 14px; border-radius:10px; border:1px solid var(--border-color);">
            <label style="font-size:12px; font-weight:600; color:var(--text-primary); margin-bottom:6px; display:block;">主界面文字字体颜色:</label>
            <div style="display:flex; align-items:center; gap:10px;">
              <input type="color" id="set-custom-text-color" style="width:36px; height:32px; border:none; border-radius:6px; cursor:pointer; background:transparent;" onchange="SettingsPlugin.onLiveAppearanceChange()">
              <input type="text" id="txt-custom-text-color" class="input-text" style="flex:1; padding:5px 8px; font-size:12px;" placeholder="默认跟随主题" readonly>
              <button class="btn btn-outline" style="padding:4px 8px; font-size:11px;" onclick="SettingsPlugin.clearCustomTextColor()">重置</button>
            </div>
          </div>

          <div style="background:var(--sidebar-active); padding:12px 14px; border-radius:10px; border:1px solid var(--border-color);">
            <label style="font-size:12px; font-weight:600; color:var(--text-primary); margin-bottom:6px; display:block;">主题强调主色调:</label>
            <div style="display:flex; align-items:center; gap:10px;">
              <input type="color" id="set-custom-primary-color" style="width:36px; height:32px; border:none; border-radius:6px; cursor:pointer; background:transparent;" onchange="SettingsPlugin.onLiveAppearanceChange()">
              <input type="text" id="txt-custom-primary-color" class="input-text" style="flex:1; padding:5px 8px; font-size:12px;" placeholder="默认经典蓝" readonly>
              <button class="btn btn-outline" style="padding:4px 8px; font-size:11px;" onclick="SettingsPlugin.clearCustomPrimaryColor()">重置</button>
            </div>
          </div>
        </div>

        <!-- 毛玻璃与透明度实时效果对照预览视窗 -->
        <div style="position:relative; width:100%; height:110px; border-radius:14px; overflow:hidden; margin-bottom:14px; border:1px solid var(--border-color); display:flex; align-items:center; justify-content:center; background:linear-gradient(135deg, #3B82F6 0%, #8B5CF6 50%, #EC4899 100%);">
          <!-- 预览背景几何装饰图块，提供强烈的透视参照 -->
          <div style="position:absolute; width:60px; height:60px; background:#FBBF24; border-radius:12px; top:15px; left:25%; transform:rotate(25deg); opacity:0.9;"></div>
          <div style="position:absolute; width:70px; height:70px; background:#10B981; border-radius:50%; bottom:10px; right:28%; opacity:0.85;"></div>
          <div style="position:absolute; width:45px; height:45px; background:#FFFFFF; border-radius:8px; top:35px; right:15%; transform:rotate(-15deg); opacity:0.7;"></div>

          <!-- 浮动在上方受控的毛玻璃测试卡片 -->
          <div id="appearance-live-preview" style="position:relative; z-index:2; width:75%; padding:12px 20px; border-radius:12px; border:1px solid rgba(255,255,255,0.4); display:flex; justify-content:space-between; align-items:center; box-shadow:0 8px 32px rgba(0,0,0,0.18);">
            <div>
              <div style="font-weight:700; font-size:13px; color:var(--text-primary);">毛玻璃与透明度实时效果验证</div>
              <div style="font-size:11px; color:var(--text-secondary); margin-top:2px;">拖拽下方滑块即时渲染，全局所有卡片与此处同步变化</div>
            </div>
            <span style="font-size:11px; padding:3px 10px; border-radius:20px; background:var(--primary); color:#FFF; font-weight:600;">Fluent Glass</span>
          </div>
        </div>

        <!-- UI 组件透明度调节与玻璃样式程度调节滑块 -->
        <div style="display:grid; grid-template-columns:repeat(2, 1fr); gap:14px; margin-bottom:10px;">
          <div style="background:var(--sidebar-active); padding:12px 14px; border-radius:10px; border:1px solid var(--border-color);">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
              <span style="font-size:12px; font-weight:600; color:var(--text-primary);">UI 组件透明度:</span>
              <span id="val-ui-opacity" style="font-size:12px; font-weight:700; color:var(--primary);">88%</span>
            </div>
            <input type="range" id="slider-ui-opacity" min="0.25" max="1.0" step="0.05" value="0.88" style="width:100%; accent-color:var(--primary); cursor:pointer;" oninput="SettingsPlugin.onLiveAppearanceChange()">
            <div style="display:flex; justify-content:space-between; font-size:10px; color:var(--text-secondary); margin-top:4px;">
              <span>高透 (25%)</span>
              <span>半透平衡 (88%)</span>
              <span>纯实色 (100%)</span>
            </div>
          </div>

          <div style="background:var(--sidebar-active); padding:12px 14px; border-radius:10px; border:1px solid var(--border-color);">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
              <span style="font-size:12px; font-weight:600; color:var(--text-primary);">玻璃样式程度 (毛玻璃模糊 Blur):</span>
              <span id="val-ui-blur" style="font-size:12px; font-weight:700; color:var(--primary);">16 px</span>
            </div>
            <input type="range" id="slider-ui-blur" min="0" max="30" step="1" value="16" style="width:100%; accent-color:var(--primary); cursor:pointer;" oninput="SettingsPlugin.onLiveAppearanceChange()">
            <div style="display:flex; justify-content:space-between; font-size:10px; color:var(--text-secondary); margin-top:4px;">
              <span>无模糊 (0px)</span>
              <span>清透拟态 (16px)</span>
              <span>深景深 (30px)</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 2. 核心调度模式与调频偏好 -->
      <div class="card">
        <h3 style="font-size:14px; font-weight:700; margin-bottom:14px;">核心调度策略与调频偏好</h3>

        <!-- 调度模式选择 (焦点模式 vs 排队器模式) -->
        <div class="form-row" style="background:var(--sidebar-active); padding:14px; border-radius:10px; border:1px solid var(--border-color); margin-bottom:14px;">
          <label style="color:var(--primary); font-size:13px; font-weight:700;">应用调优调度模式:</label>
          <select id="set-schedule-mode" class="input-text" style="margin-bottom:8px;" onchange="SettingsPlugin.onScheduleModeChanged()">
            <option value="focus">焦点窗口模式 (推荐：同时打开多个应用时，仅应用当前前台交互焦点窗口的策略)</option>
            <option value="queue">排队器模式 (优先级排队：按照排队器预设顺序依次检索，仅应用第一个正在运行的应用)</option>
          </select>
          <div id="queue-entry-hint" style="font-size:11px; color:var(--text-secondary); display:flex; justify-content:space-between; align-items:center;">
            <span>* 焦点模式仅激活当前焦点窗口；排队器模式下可在排队器中随时调整应用生效次序。</span>
            <button class="btn btn-outline" style="padding:2px 8px; font-size:11px;" onclick="App.navTo('queue')">前往配置排队顺序 &gt;</button>
          </div>
        </div>

        <!-- 调优生效继承逻辑 (单独逻辑 vs 分组继承逻辑) -->
        <div class="form-row" style="background:var(--sidebar-active); padding:12px; border-radius:8px; border:1px solid var(--border-color); margin-bottom:14px;">
          <label style="color:var(--primary); font-size:13px; font-weight:600;">调优策略生效逻辑模式:</label>
          <select id="set-policy-mode" class="input-text" style="margin-bottom:6px;">
            <option value="individual">单独应用逻辑 (推荐：每个软件独立定制，可在详情页手动导入分组配置)</option>
            <option value="group">分组继承逻辑 (自动继承：应用默认实时套用所属分组配置，支持单独覆盖脱离)</option>
          </select>
          <div style="font-size:11px; color:var(--text-secondary);">
            * 单独应用逻辑需在详情页点击【采用所属分组配置】生效；分组继承逻辑下应用将默认实时继承组内策略。
          </div>
        </div>

        <!-- 自动启动监控开关 -->
        <div class="form-row" style="padding:10px 14px; border:1px solid var(--border-color); border-radius:10px; margin-bottom:14px;">
          <label style="display:flex; align-items:center; justify-content:space-between; cursor:pointer;">
            <div>
              <div style="font-size:13px; font-weight:600; color:var(--text-primary);">启动应用时自动开启监控</div>
              <div style="font-size:11px; color:var(--text-secondary); margin-top:2px;">
                开启后，打开 Nanako App Manager 后无需手动操作，自动开启后台检测与调控。
              </div>
            </div>
            <input type="checkbox" id="set-auto-start-monitor" style="width:20px; height:20px; accent-color:var(--primary);">
          </label>
        </div>

        <!-- 全局模式开关 (含任意打开统计说明) -->
        <div class="form-row" style="padding:10px 14px; border:1px solid var(--border-color); border-radius:10px; margin-bottom:14px;">
          <label style="display:flex; align-items:center; justify-content:space-between; cursor:pointer;">
            <div>
              <div style="font-size:13px; font-weight:600; color:var(--text-primary);">启用全局识别与统计模式 (接管外部启动的应用)</div>
              <div style="font-size:11px; color:var(--text-secondary); margin-top:2px;">
                开启后，即使从桌面快捷方式、Steam 或外部文件夹打开应用，启动器也会自动接管调控，并在此情况下精准累计打开运行次数；关闭后仅接管由管理器启动的实例。
              </div>
            </div>
            <input type="checkbox" id="set-global-mode" style="width:20px; height:20px; accent-color:var(--primary);">
          </label>
        </div>

        <!-- 显卡调频缓冲器与步长体系 -->
        <div class="form-row" style="padding:12px 14px; border:1px solid var(--border-color); border-radius:10px; margin-bottom:14px;">
          <label style="display:flex; align-items:center; justify-content:space-between; cursor:pointer; margin-bottom:8px;">
            <div>
              <div style="font-size:13px; font-weight:600; color:var(--text-primary);">启用显卡调频平滑缓冲器 (Slew-Rate Buffer)</div>
              <div style="font-size:11px; color:var(--text-secondary); margin-top:2px;">
                在大幅度调频或恢复默认时，通过微步阶梯渐变过渡频率，避免核心电压骤变冲击显卡供电模块。
              </div>
            </div>
            <input type="checkbox" id="set-gpu-buffer" style="width:20px; height:20px; accent-color:var(--primary);">
          </label>
          <div style="display:flex; align-items:center; gap:20px; margin-top:10px;">
            <div style="display:flex; align-items:center; gap:8px;">
              <span style="font-size:12px; color:var(--text-secondary);">单步跨度:</span>
              <select id="set-gpu-ramp-step" class="input-text" style="width:130px; padding:4px 8px;">
                <option value="50">50 MHz (极细微步)</option>
                <option value="100">100 MHz (平缓细腻)</option>
                <option value="150" selected>150 MHz (标准推荐)</option>
                <option value="250">250 MHz (快速响应)</option>
              </select>
            </div>
            <div style="display:flex; align-items:center; gap:8px;">
              <span style="font-size:12px; color:var(--text-secondary);">步进间隔:</span>
              <select id="set-gpu-ramp-delay" class="input-text" style="width:130px; padding:4px 8px;">
                <option value="0.02">20 ms (极速过渡)</option>
                <option value="0.035" selected>35 ms (平稳均衡)</option>
                <option value="0.05">50 ms (保守稳定)</option>
              </select>
            </div>
          </div>
        </div>

        <!-- 运行日志记录开关 -->
        <div class="form-row" style="padding:10px 14px; border:1px solid var(--border-color); border-radius:10px; margin-bottom:14px;">
          <label style="display:flex; align-items:center; justify-content:space-between; cursor:pointer;">
            <div>
              <div style="font-size:13px; font-weight:600; color:var(--text-primary);">启用调度与运行日志</div>
              <div style="font-size:11px; color:var(--text-secondary); margin-top:2px;">
                记录应用的窗口焦点状态与频率变动；关闭后将停止写入日志，减少系统 I/O 与界面刷新开销。
              </div>
            </div>
            <input type="checkbox" id="set-enable-logging" style="width:20px; height:20px; accent-color:var(--primary);">
          </label>
        </div>
      </div>

      <!-- 3. 系统与第三方联动偏好 -->
      <div class="card">
        <h3 style="font-size:14px; font-weight:700; margin-bottom:14px;">系统与第三方生态偏好</h3>

        <div class="form-row">
          <label style="display:flex; align-items:center; gap:8px; cursor:pointer;">
            <input type="checkbox" id="set-auto-msi" style="width:16px; height:16px; accent-color:var(--primary);">
            <span>打开应用/开启调度时自动启动微星小飞机 (MSI Afterburner)</span>
          </label>
        </div>

        <div class="form-row">
          <label style="display:flex; align-items:center; gap:8px; cursor:pointer;">
            <input type="checkbox" id="set-autostart" style="width:16px; height:16px; accent-color:var(--primary);">
            <span>开机自动启动 Nanako App Manager 管理器主程序</span>
          </label>
        </div>

        <div class="form-row">
          <label>全局调度启停快捷键:</label>
          <select id="set-hotkey">
            <option value="F12">F12</option>
            <option value="Ctrl+F12">Ctrl+F12</option>
            <option value="无">无</option>
          </select>
        </div>

        <!-- 网页在线搜索跳转配置 -->
        <div class="form-row" style="margin-top:14px;">
          <label style="display:flex; align-items:center; gap:8px; cursor:pointer;">
            <input type="checkbox" id="set-web-search" style="width:16px; height:16px; accent-color:var(--primary);" onchange="SettingsPlugin.toggleWebSearchSettings(this.checked)">
            <span>启用点击详情页软件标题跳转浏览器检索</span>
          </label>
        </div>

        <div id="web-search-config-group" style="margin-left:24px; margin-bottom:14px;">
          <div class="form-row">
            <label>默认检索搜索引擎 / 平台:</label>
            <select id="set-search-engine" onchange="SettingsPlugin.onSearchEngineChange()">
              <option value="bing">必应 (Bing)</option>
              <option value="google">谷歌 (Google)</option>
              <option value="baidu">百度 (Baidu)</option>
              <option value="bilibili">哔哩哔哩 (Bilibili)</option>
              <option value="github">GitHub</option>
              <option value="custom">自定义搜索 URL 模板</option>
            </select>
          </div>
          <div class="form-row" id="row-custom-search-url" style="display:none;">
            <label>自定义搜索 URL 模板 ({keyword} 代表搜索词):</label>
            <input type="text" id="set-custom-search-url" class="input-text" placeholder="https://search.bilibili.com/all?keyword={keyword}&from_source=webhistory_search">
          </div>
        </div>

        <!-- 全局网络代理 -->
        <div style="margin-top:18px; padding-top:14px; border-top:1px solid var(--border-color);">
          <h3 style="font-size:14px; font-weight:700; margin-bottom:4px; color:var(--text-primary);">全局网络代理设置</h3>
          <p style="font-size:12px; color:var(--text-secondary); margin-bottom:12px;">设置全局代理服务器地址后网络请求优先走此代理；留空则直接使用系统默认网络设置。</p>
          <div class="form-row">
            <label style="font-size:12px; color:var(--text-secondary);">全局代理服务器地址 (例如: http://127.0.0.1:7890 或 socks5://127.0.0.1:1080)</label>
            <input type="text" id="set-global-proxy" class="proxy-input-pill" placeholder="">
          </div>
        </div>

        <div style="display:flex; align-items:center; gap:12px; margin-top:10px;">
          <button class="btn" onclick="SettingsPlugin.saveSettings()">保存系统偏好设置</button>
          <span id="txt-settings-feedback" style="font-size:12px; color:var(--success); font-weight:600; display:none;">● 系统偏好与外观参数已保存至配置文件 (详见日志)</span>
        </div>
      </div>

      <!-- 4. 数据备份与恢复 -->
      <div class="card">
        <h3 style="font-size:14px; font-weight:700; margin-bottom:10px;">数据备份与恢复</h3>
        <p style="font-size:12px; color:var(--text-secondary); margin-bottom:14px;">所有对启动器的修改、调控策略与个性化外观参数均统一保存在 JSON 数据库文件中，可随时一键导出与恢复。</p>
        <div style="display:flex; gap:12px;">
          <button class="btn" onclick="SettingsPlugin.exportBackupData()">
            <svg viewBox="0 0 24 24"><path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96zM17 13l-5 5-5-5h3V9h4v4h3z"/></svg>
            <span>一键备份所有配置 (导出 JSON)</span>
          </button>
          <button class="btn btn-outline" onclick="SettingsPlugin.importBackupData()">
            <svg viewBox="0 0 24 24"><path d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96zM14 13v4h-4v-4H7l5-5 5 5h-3z"/></svg>
            <span>恢复数据 (导入备份)</span>
          </button>
        </div>
      </div>

      <!-- 5. 运行日志查看面板 -->
      <div class="card">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
          <h3 style="font-size:14px; font-weight:700;">系统运行全局日志</h3>
          <button class="btn btn-outline" style="padding:2px 8px; font-size:11px;" onclick="SettingsPlugin.clearLogs()">清空日志</button>
        </div>
        <div id="global-log-box" class="log-console" style="height:160px;"></div>
      </div>
    `;
  },

  async onActivate() {
    const s = await window.pywebview.api.get_settings();
    App.systemSettings = s;

    // 1. 初始化外观设置组件
    this.initAppearanceUI(s);

    // 2. 初始化核心参数
    document.getElementById('set-schedule-mode').value = s.schedule_mode || 'focus';
    this.onScheduleModeChanged();

    document.getElementById('set-policy-mode').value = s.policy_mode || 'individual';
    document.getElementById('set-auto-start-monitor').checked = (s.auto_start_monitor !== false);
    document.getElementById('set-global-mode').checked = (s.global_mode !== false);
    document.getElementById('set-enable-logging').checked = (s.enable_logging !== false);
    document.getElementById('set-gpu-buffer').checked = (s.enable_gpu_buffer !== false);
    document.getElementById('set-gpu-ramp-step').value = String(s.gpu_ramp_step || 150);
    document.getElementById('set-gpu-ramp-delay').value = String(s.gpu_ramp_delay || 0.035);

    document.getElementById('set-auto-msi').checked = (s.auto_launch_msi !== false);
    document.getElementById('set-autostart').checked = (s.auto_start || false);
    document.getElementById('set-hotkey').value = s.hotkey || 'F12';

    const webSearchEnabled = (s.enable_web_search !== false);
    document.getElementById('set-web-search').checked = webSearchEnabled;
    this.toggleWebSearchSettings(webSearchEnabled);

    document.getElementById('set-search-engine').value = s.search_engine || 'bing';
    document.getElementById('set-custom-search-url').value = s.custom_search_url || '';
    this.onSearchEngineChange();

    document.getElementById('set-global-proxy').value = s.global_proxy || '';
  },

  initAppearanceUI(s) {
    // 壁纸预览
    const pBox = document.getElementById('wallpaper-preview-box');
    const pHint = document.getElementById('txt-wallpaper-hint');
    if (s.custom_wallpaper && s.custom_wallpaper.trim()) {
      if (pBox) pBox.style.backgroundImage = `url("${s.custom_wallpaper.trim()}")`;
      if (pHint) pHint.style.display = 'none';
    } else {
      if (pBox) pBox.style.backgroundImage = '';
      if (pHint) pHint.style.display = 'block';
    }

    // 字体与主色
    const tColorInput = document.getElementById('set-custom-text-color');
    const tColorTxt = document.getElementById('txt-custom-text-color');
    if (s.custom_text_color) {
      tColorInput.value = s.custom_text_color;
      tColorTxt.value = s.custom_text_color;
    } else {
      tColorInput.value = '#1E293B';
      tColorTxt.value = '默认跟随主题';
    }

    const pColorInput = document.getElementById('set-custom-primary-color');
    const pColorTxt = document.getElementById('txt-custom-primary-color');
    if (s.custom_primary_color) {
      pColorInput.value = s.custom_primary_color;
      pColorTxt.value = s.custom_primary_color;
    } else {
      pColorInput.value = '#2563EB';
      pColorTxt.value = '默认经典蓝 (#2563EB)';
    }

    // 透明度与模糊
    const op = (s.ui_opacity !== undefined && s.ui_opacity !== null) ? parseFloat(s.ui_opacity) : 0.90;
    document.getElementById('slider-ui-opacity').value = op;
    document.getElementById('val-ui-opacity').innerText = Math.round(op * 100) + '%';

    const blur = (s.ui_blur !== undefined && s.ui_blur !== null) ? parseInt(s.ui_blur) : 16;
    document.getElementById('slider-ui-blur').value = blur;
    document.getElementById('val-ui-blur').innerText = blur + ' px';
  },

  onLiveAppearanceChange() {
    const tColor = document.getElementById('set-custom-text-color').value;
    const pColor = document.getElementById('set-custom-primary-color').value;
    const op = parseFloat(document.getElementById('slider-ui-opacity').value);
    const blur = parseInt(document.getElementById('slider-ui-blur').value);

    document.getElementById('txt-custom-text-color').value = tColor;
    document.getElementById('txt-custom-primary-color').value = pColor;
    document.getElementById('val-ui-opacity').innerText = Math.round(op * 100) + '%';
    document.getElementById('val-ui-blur').innerText = blur + ' px';

    // 实时作用于界面，无需刷新
    App.applyAppearanceSettings({
      custom_wallpaper: App.systemSettings.custom_wallpaper || '',
      custom_wallpaper_fit: App.systemSettings.custom_wallpaper_fit || 'cover',
      custom_text_color: tColor,
      custom_primary_color: pColor,
      ui_opacity: op,
      ui_blur: blur,
      sidebar_collapsed: App.isSidebarCollapsed
    });
  },

  clearCustomTextColor() {
    document.getElementById('set-custom-text-color').value = '#1E293B';
    document.getElementById('txt-custom-text-color').value = '默认跟随主题';
    document.documentElement.style.removeProperty('--text-primary');
    this.onLiveAppearanceChange();
  },

  clearCustomPrimaryColor() {
    document.getElementById('set-custom-primary-color').value = '#2563EB';
    document.getElementById('txt-custom-primary-color').value = '默认经典蓝 (#2563EB)';
    document.documentElement.style.removeProperty('--primary');
    document.documentElement.style.removeProperty('--primary-hover');
    this.onLiveAppearanceChange();
  },

  async chooseWallpaper() {
    const res = await window.pywebview.api.browse_wallpaper_file();
    if (res && res.success && res.wallpaper) {
      App.systemSettings.custom_wallpaper = res.wallpaper;
      this.initAppearanceUI(App.systemSettings);
      App.applyAppearanceSettings(App.systemSettings);
      // 已在日志中记录完成
    }
  },

  async removeWallpaper() {
    await window.pywebview.api.clear_wallpaper();
    App.systemSettings.custom_wallpaper = '';
    this.initAppearanceUI(App.systemSettings);
    App.applyAppearanceSettings(App.systemSettings);
    // 已在日志中记录完成
  },

  async resetAppearance() {
    const res = await window.pywebview.api.reset_appearance_settings();
    if (res && res.success) {
      App.systemSettings = res.settings;
      this.initAppearanceUI(App.systemSettings);
      App.applyAppearanceSettings(App.systemSettings);
      // 已在日志中记录完成
    }
  },

  onScheduleModeChanged() {
    const mode = document.getElementById('set-schedule-mode').value;
    const hintEl = document.getElementById('queue-entry-hint');
    if (hintEl) {
      hintEl.style.display = (mode === 'queue') ? 'flex' : 'none';
    }
  },

  toggleWebSearchSettings(enabled) {
    const group = document.getElementById('web-search-config-group');
    if (group) group.style.display = enabled ? 'block' : 'none';
  },

  onSearchEngineChange() {
    const sel = document.getElementById('set-search-engine').value;
    const customRow = document.getElementById('row-custom-search-url');
    if (customRow) customRow.style.display = (sel === 'custom') ? 'block' : 'none';
  },

  validateProxyUrl(proxy) {
    if (!proxy || !proxy.trim()) return true;
    const reg = /^(http|https|socks4|socks5):\/\/[a-zA-Z0-9.\-_]+:\d{1,5}$/i;
    return reg.test(proxy.trim());
  },

  async saveSettings() {
    const globalProxyVal = document.getElementById('set-global-proxy').value.trim();
    if (!this.validateProxyUrl(globalProxyVal)) {
      return alert("全局代理服务器地址格式错误！\n\n请遵循规范格式: 协议://IP或域名:端口\n例如: http://127.0.0.1:7890 或 socks5://127.0.0.1:1080\n若不配置代理请直接留空。");
    }

    const tColorVal = document.getElementById('txt-custom-text-color').value.includes('默认') ? '' : document.getElementById('set-custom-text-color').value;
    const pColorVal = document.getElementById('txt-custom-primary-color').value.includes('默认') ? '' : document.getElementById('set-custom-primary-color').value;

    const s = {
      schedule_mode: document.getElementById('set-schedule-mode').value,
      policy_mode: document.getElementById('set-policy-mode').value,
      auto_start_monitor: document.getElementById('set-auto-start-monitor').checked,
      global_mode: document.getElementById('set-global-mode').checked,
      enable_logging: document.getElementById('set-enable-logging').checked,
      enable_gpu_buffer: document.getElementById('set-gpu-buffer').checked,
      gpu_ramp_step: parseInt(document.getElementById('set-gpu-ramp-step').value || 150),
      gpu_ramp_delay: parseFloat(document.getElementById('set-gpu-ramp-delay').value || 0.035),
      auto_launch_msi: document.getElementById('set-auto-msi').checked,
      auto_start: document.getElementById('set-autostart').checked,
      hotkey: document.getElementById('set-hotkey').value,
      enable_web_search: document.getElementById('set-web-search').checked,
      search_engine: document.getElementById('set-search-engine').value,
      custom_search_url: document.getElementById('set-custom-search-url').value.trim(),
      global_proxy: globalProxyVal,
      queue_order: App.systemSettings.queue_order || [],

      // 持久化外观配置至 JSON
      custom_wallpaper: App.systemSettings.custom_wallpaper || '',
      custom_wallpaper_fit: App.systemSettings.custom_wallpaper_fit || 'cover',
      custom_text_color: tColorVal,
      custom_primary_color: pColorVal,
      ui_opacity: parseFloat(document.getElementById('slider-ui-opacity').value),
      ui_blur: parseInt(document.getElementById('slider-ui-blur').value),
      sidebar_collapsed: App.isSidebarCollapsed
    };

    await window.pywebview.api.save_settings(s);
    App.systemSettings = s;
    App.applyAppearanceSettings(s);
    const fb = document.getElementById('txt-settings-feedback');
    if (fb) {
      fb.style.display = 'inline';
      setTimeout(() => { fb.style.display = 'none'; }, 2600);
    }

    const modeBadge = document.getElementById('top-mode-badge');
    if (modeBadge) {
      modeBadge.innerText = (s.schedule_mode === 'queue') ? '排队模式' : '焦点模式';
    }

    // 已在日志中记录完成
  },

  async exportBackupData() {
    const res = await window.pywebview.api.export_backup();
    if (res && res.success) {
      // 已在日志中记录完成
    }
  },

  async importBackupData() {
    if (confirm('导入备份将会覆盖现有所有软件库与分组配置，是否继续？')) {
      const res = await window.pywebview.api.import_backup();
      if (res && res.success) {
        // 已在日志中记录完成
        await App.init();
      } else if (res && !res.cancelled) {
        alert(res.msg || res.error);
      }
    }
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

App.registerPlugin(SettingsPlugin);
