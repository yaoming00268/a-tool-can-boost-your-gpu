const LibraryPlugin = {
  id: "library",
  title: "软件库",
  order: 20,
  isNavItem: true,
  icon: `<svg viewBox="0 0 24 24"><path d="M4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm16-4H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H8V4h12v12z"/></svg>`,
  currentCategory: "全部",
  currentSortBy: "last_run",
  currentSortOrder: "desc",

  renderView() {
    return `
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
        <div id="category-pills" style="display:flex; gap:8px;"></div>
      </div>
      <div id="library-app-grid" class="app-grid"></div>
    `;
  },

  renderModal() {
    return `
      <div id="filter-dropdown" class="custom-popup-menu" style="width:280px; padding:16px;" onclick="event.stopPropagation()">
        <div style="font-weight:700; font-size:13px; margin-bottom:10px;">排序方式</div>
        <select id="sort-by-select" class="input-text" style="margin-bottom:8px;" onchange="LibraryPlugin.refresh()">
          <option value="last_run">最近运行时间</option>
          <option value="launch_count">启动打开次数</option>
          <option value="name">软件名称 (A-Z)</option>
          <option value="add_time">添加时间</option>
        </select>
        <div style="display:flex; gap:8px; margin-bottom:14px;">
          <button id="btn-sort-desc" class="btn" style="flex:1;" onclick="LibraryPlugin.setSortOrder('desc')">降序排列</button>
          <button id="btn-sort-asc" class="btn btn-outline" style="flex:1;" onclick="LibraryPlugin.setSortOrder('asc')">升序排列</button>
        </div>
      </div>
    `;
  },

  async onActivate() {
    await this.refresh();
  },

  async refresh() {
    const cats = await window.pywebview.api.get_categories();
    const pills = document.getElementById('category-pills');
    if (pills) {
      pills.innerHTML = cats.map(c => `
        <button class="btn ${c === this.currentCategory ? '' : 'btn-outline'}" onclick="event.stopPropagation(); LibraryPlugin.filterCategory('${c}')">${c}</button>
      `).join('');
    }

    const query = document.getElementById('global-search').value;
    const apps = await window.pywebview.api.get_apps(this.currentCategory, query, this.currentSortBy, this.currentSortOrder, "全部", false);
    const grid = document.getElementById('library-app-grid');
    if (grid) grid.innerHTML = apps.map(a => this.renderCard(a)).join('');
  },

  renderCard(a) {
    const isChecked = App.selectedAppIds.has(a.id) ? 'checked' : '';
    const isSelected = (App.singleSelectedAppId === a.id || App.selectedAppIds.has(a.id)) ? 'selected' : '';
    const effectiveGpuMode = a.effective_tuning ? a.effective_tuning.gpu_mode : (a.gpu_mode || '默认策略');

    return `
      <div class="app-card ${isSelected}" data-id="${a.id}" 
           onclick="LibraryPlugin.handleCardClick(event, '${a.id}')" 
           ondblclick="App.navTo('detail', { appId: '${a.id}', name: '${a.name.replace(/'/g, "\\'")}' })"
           oncontextmenu="ModalsPlugin.openAppContextMenu(event, '${a.id}')">
        <input type="checkbox" class="multi-select-checkbox" ${isChecked} onclick="event.stopPropagation(); LibraryPlugin.toggleSelect('${a.id}')">
        <div class="selection-check-badge" title="当前已选中"><svg viewBox="0 0 24 24"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg></div>
        <img src="${a.icon}">
        <div style="font-weight:700; font-size:13px; max-width:150px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${a.name}</div>
        <div style="font-size:11px; color:var(--text-secondary); margin-top:2px;">打开 ${a.launch_count || 0} 次</div>
        <div class="app-chip">${effectiveGpuMode}</div>
      </div>
    `;
  },

  handleCardClick(e, appId) {
    e.stopPropagation();
    if (App.isMultiSelect) {
      this.toggleSelect(appId);
      return;
    }
    App.singleSelectedAppId = (App.singleSelectedAppId === appId) ? null : appId;
    document.querySelectorAll('.app-card').forEach(c => {
      c.classList.toggle('selected', c.getAttribute('data-id') === App.singleSelectedAppId);
    });
  },

  toggleSelect(appId) {
    if (App.selectedAppIds.has(appId)) App.selectedAppIds.delete(appId);
    else App.selectedAppIds.add(appId);
    document.getElementById('batch-count-text').innerText = `已选择 ${App.selectedAppIds.size} 项`;
    this.refresh();
  },

  filterCategory(c) {
    this.currentCategory = c;
    this.refresh();
  },

  toggleFilterDropdown(e) {
    e.stopPropagation();
    const d = document.getElementById('filter-dropdown');
    d.style.display = d.style.display === 'block' ? 'none' : 'block';
    d.style.top = "60px";
    d.style.right = "24px";
  },

  setSortOrder(order) {
    this.currentSortOrder = order;
    document.getElementById('btn-sort-desc').className = order === 'desc' ? 'btn' : 'btn btn-outline';
    document.getElementById('btn-sort-asc').className = order === 'asc' ? 'btn' : 'btn btn-outline';
    this.refresh();
  },

  async batchLaunch() {
    for (const id of App.selectedAppIds) await window.pywebview.api.launch_app(id);
    App.toggleMultiSelectMode();
  },

  async batchKill() {
    for (const id of App.selectedAppIds) await window.pywebview.api.terminate_app(id);
    App.toggleMultiSelectMode();
  },

  async batchDelete() {
    if (confirm(`确定要批量删除选中的 ${App.selectedAppIds.size} 个软件吗？`)) {
      await window.pywebview.api.batch_delete_apps(Array.from(App.selectedAppIds));
      App.toggleMultiSelectMode();
      this.refresh();
    }
  },

  async promptBatchCategory() {
    const cats = await window.pywebview.api.get_categories();
    const target = prompt(`输入目标分类名称 (${cats.join(', ')}):`);
    if (target) {
      await window.pywebview.api.batch_set_category(Array.from(App.selectedAppIds), target);
      App.toggleMultiSelectMode();
      this.refresh();
    }
  }
};

App.registerPlugin(LibraryPlugin);
