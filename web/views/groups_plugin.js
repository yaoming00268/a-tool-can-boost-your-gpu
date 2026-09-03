const GroupsPlugin = {
  id: "groups",
  title: "分组",
  order: 40,
  isNavItem: true,
  icon: `<svg viewBox="0 0 24 24"><path d="M10 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z"/></svg>`,
  contextCat: null,

  renderView() {
    return `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
        <div>
          <h2 style="font-size:18px; font-weight:700;">全部分组与统一调控管理</h2>
          <div style="font-size:12px; color:var(--text-secondary); margin-top:3px;">
            左键点击进入组内筛选；右键任一分组可执行【删除该分组】、【重命名】与【统一硬件调控配置】
          </div>
        </div>
        <button class="btn" onclick="GroupsPlugin.promptAdd()">
          <svg viewBox="0 0 24 24"><path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/></svg>
          <span>添加新分组</span>
        </button>
      </div>

      <div id="groups-container" style="display:grid; grid-template-columns:repeat(auto-fill, minmax(260px, 1fr)); gap:16px;"></div>
    `;
  },

  async onActivate() {
    const cats = await window.pywebview.api.get_categories();
    const allApps = await window.pywebview.api.get_apps();
    const container = document.getElementById('groups-container');
    
    container.innerHTML = cats.filter(c => c !== '全部').map(c => {
      const count = allApps.filter(a => a.category === c).length;
      return `
        <div class="card group-card" style="cursor:pointer; margin-bottom:0;" 
             onclick="LibraryPlugin.filterCategory('${c}'); App.navTo('library');"
             oncontextmenu="GroupsPlugin.openCategoryContextMenu(event, '${c}')">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <div style="display:flex; align-items:center; gap:10px;">
              <div style="width:36px; height:36px; border-radius:10px; background:var(--sidebar-active); display:flex; align-items:center; justify-content:center;">
                <svg viewBox="0 0 24 24" style="width:20px; height:20px; fill:var(--primary);"><path d="M10 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z"/></svg>
              </div>
              <div>
                <div style="font-weight:700; font-size:14px; color:var(--text-primary);">${c}</div>
                <div style="font-size:11px; color:var(--text-secondary); margin-top:2px;">右键管理 / 配置统一策略</div>
              </div>
            </div>
            <div style="display:flex; flex-direction:column; align-items:flex-end; gap:6px;">
              <span class="app-chip" style="margin-top:0;">${count} 个软件</span>
              <button class="btn btn-outline" style="padding:2px 8px; font-size:10px; border-radius:6px;" onclick="event.stopPropagation(); GroupsPlugin.openPolicyModal('${c}')" title="配置该分组统一调优策略">统一调控</button>
            </div>
          </div>
        </div>
      `;
    }).join('');
  },

  async promptAdd() {
    const name = prompt('请输入新分组名称:');
    if (name && name.trim()) {
      await window.pywebview.api.add_category(name.trim());
      this.onActivate();
    }
  },

  // 1. 右键呼出分组专属上下文菜单
  openCategoryContextMenu(e, catName) {
    e.preventDefault();
    e.stopPropagation();
    this.contextCat = catName;
    const menu = document.getElementById('group-context-menu');
    if (!menu) return;
    menu.style.display = 'block';
    menu.style.left = Math.min(e.clientX, window.innerWidth - 220) + 'px';
    menu.style.top = Math.min(e.clientY, window.innerHeight - 240) + 'px';
  },

  ctxViewApps() {
    if (this.contextCat) {
      LibraryPlugin.filterCategory(this.contextCat);
      App.navTo('library');
    }
  },

  ctxConfigPolicy() {
    if (this.contextCat) {
      this.openPolicyModal(this.contextCat);
    }
  },

  async ctxSyncToApps() {
    if (this.contextCat) {
      if (confirm(`确定要将【${this.contextCat}】分组的统一调优策略强制同步给组内所有软件吗？\\n这将会重置组内软件的独立定制标记。`)) {
        const res = await window.pywebview.api.sync_group_config_to_apps(this.contextCat);
        // 结果在日志中展示
      }
    }
  },

  async ctxRename() {
    if (this.contextCat) {
      if (this.contextCat === '常用工具') return alert('系统默认「常用工具」分组不支持重命名');
      const newName = prompt(`请输入分组【${this.contextCat}】的新名称:`, this.contextCat);
      if (newName && newName.trim() && newName.trim() !== this.contextCat) {
        const res = await window.pywebview.api.rename_category(this.contextCat, newName.trim());
        if (res.success) {
          // 结果在日志中展示
          this.onActivate();
        } else {
          alert(res.msg || "重命名失败");
        }
      }
    }
  },

  // 2. 右键执行删除该分组操作 (需求4核心)
  async ctxDeleteGroup() {
    if (!this.contextCat) return;
    if (this.contextCat === '常用工具') {
      return alert('「常用工具」为系统保留默认基础分组，不能删除。');
    }

    if (confirm(`【警告】确定要删除分组【${this.contextCat}】吗？\\n\\n该分组被删除后，组内的所有软件不会被移除，将自动安全移入【常用工具】分组中。`)) {
      const ok = await window.pywebview.api.delete_category(this.contextCat);
      if (ok) {
        // 结果在日志中展示
        this.contextCat = null;
        this.onActivate();
        if (LibraryPlugin.refresh) LibraryPlugin.refresh();
      } else {
        alert("删除分组失败，请重试。");
      }
    }
  },

  // 3. 分组统一调控策略模态框 (需求5: 完全恢复被误删的分组调节逻辑)
  async openPolicyModal(catName) {
    this.contextCat = catName;
    const gCfg = await window.pywebview.api.get_group_config(catName);

    document.getElementById('title-group-config').innerText = `【${catName}】分组统一调优策略配置`;
    document.getElementById('modal-group-gpu-mode').value = gCfg.gpu_mode || '不修改';
    document.getElementById('modal-group-gpu-freq').value = gCfg.gpu_freq || 2000;
    document.getElementById('modal-group-gpu-min').value = gCfg.gpu_min_freq || 200;
    document.getElementById('modal-group-gpu-max').value = gCfg.gpu_max_freq || 2400;
    this.onGroupModalModeChange();

    // 填充电源计划与 MSI
    const pSel = document.getElementById('modal-group-power-plan');
    pSel.innerHTML = '<option value="默认">跟随系统当前计划</option>' + App.allPowerPlans.map(p => `<option value="${p.guid}" ${p.guid === gCfg.power_plan_guid ? 'selected' : ''}>${p.name}</option>`).join('');

    const mSel = document.getElementById('modal-group-msi-profile');
    mSel.innerHTML = '<option value="默认配置">默认配置</option>' + App.allMsiProfiles.map(p => `<option value="${p}" ${p === gCfg.msi_profile ? 'selected' : ''}>${p}</option>`).join('');

    document.getElementById('modal-group-config').style.display = 'flex';
  },

  onGroupModalModeChange() {
    const mode = document.getElementById('modal-group-gpu-mode').value;
    document.getElementById('modal-group-fixed').style.display = (mode === '定频模式') ? 'block' : 'none';
    document.getElementById('modal-group-range').style.display = (mode === '频段模式') ? 'flex' : 'none';
  },

  async submitGroupConfig() {
    if (!this.contextCat) return;
    const mode = document.getElementById('modal-group-gpu-mode').value;
    const freq = parseInt(document.getElementById('modal-group-gpu-freq').value) || 2000;
    const minF = parseInt(document.getElementById('modal-group-gpu-min').value) || 200;
    const maxF = parseInt(document.getElementById('modal-group-gpu-max').value) || 2400;
    const pPlan = document.getElementById('modal-group-power-plan').value;
    const mProfile = document.getElementById('modal-group-msi-profile').value;

    const configData = {
      gpu_mode: mode,
      gpu_freq: freq,
      gpu_min_freq: minF,
      gpu_max_freq: maxF,
      power_plan_guid: pPlan,
      msi_profile: mProfile
    };

    await window.pywebview.api.save_group_config(this.contextCat, configData);
    ModalsPlugin.close('modal-group-config');
    alert(`【${this.contextCat}】分组的统一调优策略已保存！\\n若系统偏好设置为【分组继承逻辑】，组内继承该配置的应用将实时同步生效。`);
  },

  async submitSyncToApps() {
    if (!this.contextCat) return;
    if (confirm(`确定要保存当前配置，并强制同步重置【${this.contextCat}】组内的全部软件吗？`)) {
      await this.submitGroupConfig();
      const res = await window.pywebview.api.sync_group_config_to_apps(this.contextCat);
      // 结果在日志中展示
    }
  }
};

App.registerPlugin(GroupsPlugin);
