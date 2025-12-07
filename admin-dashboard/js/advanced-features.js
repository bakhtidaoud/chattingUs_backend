/**
 * Advanced Features & Interactions
 * Enhanced functionality for admin dashboard
 */

const AdvancedFeatures = {
  // ============================================
  // GLOBAL SEARCH
  // ============================================

  search: {
    isOpen: false,
    recentSearches: [],
    maxRecent: 5,

    init() {
      this.loadRecentSearches();
      this.setupGlobalSearch();
      this.setupKeyboardShortcuts();
    },

    setupGlobalSearch() {
      const searchInput = document.getElementById('globalSearch');
      if (!searchInput) return;

      // Autocomplete on input
      searchInput.addEventListener('input', Utils.debounce((e) => {
        this.performSearch(e.target.value);
      }, 300));

      // Handle enter key
      searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          this.executeSearch(e.target.value);
        }
      });
    },

    setupKeyboardShortcuts() {
      document.addEventListener('keydown', (e) => {
        // Ctrl+K or Cmd+K: Open search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
          e.preventDefault();
          this.openSearch();
        }

        // /: Focus search
        if (e.key === '/' && !this.isInputFocused()) {
          e.preventDefault();
          this.openSearch();
        }
      });
    },

    async performSearch(query) {
      if (!query || query.length < 2) return;

      try {
        const results = await API.get('/search/', { q: query });
        this.showSuggestions(results);
      } catch (error) {
        console.error('Search error:', error);
      }
    },

    showSuggestions(results) {
      const dropdown = document.getElementById('searchDropdown');
      if (!dropdown) return;

      dropdown.innerHTML = results.map(result => `
                <div class="search-result-item" onclick="AdvancedFeatures.search.selectResult('${result.type}', ${result.id})">
                    <i class="fas fa-${this.getIcon(result.type)}"></i>
                    <div>
                        <div class="result-title">${result.title}</div>
                        <div class="result-type">${result.type}</div>
                    </div>
                </div>
            `).join('');

      dropdown.style.display = 'block';
    },

    executeSearch(query) {
      this.saveRecentSearch(query);
      window.location.href = `/search?q=${encodeURIComponent(query)}`;
    },

    saveRecentSearch(query) {
      this.recentSearches = [query, ...this.recentSearches.filter(s => s !== query)].slice(0, this.maxRecent);
      localStorage.setItem('recentSearches', JSON.stringify(this.recentSearches));
    },

    loadRecentSearches() {
      const saved = localStorage.getItem('recentSearches');
      this.recentSearches = saved ? JSON.parse(saved) : [];
    },

    openSearch() {
      const searchInput = document.getElementById('globalSearch');
      if (searchInput) {
        searchInput.focus();
        this.isOpen = true;
      }
    },

    isInputFocused() {
      const active = document.activeElement;
      return active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA');
    },

    getIcon(type) {
      const icons = {
        user: 'user',
        post: 'image',
        story: 'circle',
        reel: 'video',
        stream: 'broadcast-tower'
      };
      return icons[type] || 'search';
    }
  },

  // ============================================
  // BULK ACTIONS
  // ============================================

  bulkActions: {
    selectedItems: new Set(),

    init() {
      this.setupSelectAll();
      this.setupIndividualCheckboxes();
      this.updateBulkActionsBar();
    },

    setupSelectAll() {
      const selectAll = document.getElementById('selectAll');
      if (!selectAll) return;

      selectAll.addEventListener('change', (e) => {
        const checkboxes = document.querySelectorAll('.item-checkbox');
        checkboxes.forEach(cb => {
          cb.checked = e.target.checked;
          if (e.target.checked) {
            this.selectedItems.add(cb.value);
          } else {
            this.selectedItems.delete(cb.value);
          }
        });
        this.updateBulkActionsBar();
      });
    },

    setupIndividualCheckboxes() {
      document.addEventListener('change', (e) => {
        if (e.target.classList.contains('item-checkbox')) {
          if (e.target.checked) {
            this.selectedItems.add(e.target.value);
          } else {
            this.selectedItems.delete(e.target.value);
          }
          this.updateBulkActionsBar();
        }
      });
    },

    updateBulkActionsBar() {
      const bar = document.getElementById('bulkActionsBar');
      const count = document.getElementById('selectedCount');

      if (this.selectedItems.size > 0) {
        if (bar) bar.style.display = 'flex';
        if (count) count.textContent = this.selectedItems.size;
      } else {
        if (bar) bar.style.display = 'none';
      }
    },

    async bulkDelete() {
      if (!confirm(`Delete ${this.selectedItems.size} items?`)) return;

      const progress = this.showProgress('Deleting items...');
      let completed = 0;

      for (const id of this.selectedItems) {
        try {
          await API.delete(`/items/${id}/`);
          completed++;
          this.updateProgress(progress, completed, this.selectedItems.size);
        } catch (error) {
          console.error(`Failed to delete item ${id}:`, error);
        }
      }

      this.hideProgress(progress);
      this.clearSelection();
      Utils.showToast(`Deleted ${completed} items`, 'success');
      window.location.reload();
    },

    async bulkExport(format = 'csv') {
      const items = Array.from(this.selectedItems);
      try {
        const data = await API.post('/export/', { ids: items, format });
        this.downloadFile(data, `export.${format}`);
        Utils.showToast('Export completed', 'success');
      } catch (error) {
        Utils.showToast('Export failed', 'error');
      }
    },

    showProgress(message) {
      const progress = document.createElement('div');
      progress.className = 'bulk-progress';
      progress.innerHTML = `
                <div class="progress-message">${message}</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: 0%"></div>
                </div>
            `;
      document.body.appendChild(progress);
      return progress;
    },

    updateProgress(element, current, total) {
      const percent = (current / total) * 100;
      const fill = element.querySelector('.progress-fill');
      if (fill) fill.style.width = `${percent}%`;
    },

    hideProgress(element) {
      element.remove();
    },

    clearSelection() {
      this.selectedItems.clear();
      document.querySelectorAll('.item-checkbox').forEach(cb => cb.checked = false);
      const selectAll = document.getElementById('selectAll');
      if (selectAll) selectAll.checked = false;
      this.updateBulkActionsBar();
    },

    downloadFile(data, filename) {
      const blob = new Blob([data], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      link.click();
      URL.revokeObjectURL(url);
    }
  },

  // ============================================
  // DRAG & DROP
  // ============================================

  dragDrop: {
    init() {
      this.setupFileUpload();
      this.setupReorder();
    },

    setupFileUpload() {
      const dropZones = document.querySelectorAll('.drop-zone');

      dropZones.forEach(zone => {
        zone.addEventListener('dragover', (e) => {
          e.preventDefault();
          zone.classList.add('drag-over');
        });

        zone.addEventListener('dragleave', () => {
          zone.classList.remove('drag-over');
        });

        zone.addEventListener('drop', (e) => {
          e.preventDefault();
          zone.classList.remove('drag-over');

          const files = e.dataTransfer.files;
          this.handleFiles(files, zone);
        });

        // Click to upload
        zone.addEventListener('click', () => {
          const input = document.createElement('input');
          input.type = 'file';
          input.multiple = true;
          input.onchange = (e) => this.handleFiles(e.target.files, zone);
          input.click();
        });
      });
    },

    handleFiles(files, zone) {
      Array.from(files).forEach(file => {
        this.uploadFile(file, zone);
      });
    },

    async uploadFile(file, zone) {
      const formData = new FormData();
      formData.append('file', file);

      const progressBar = this.createProgressBar(file.name);
      zone.appendChild(progressBar);

      try {
        const response = await fetch('/api/upload/', {
          method: 'POST',
          body: formData,
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          }
        });

        if (response.ok) {
          const data = await response.json();
          this.showPreview(data, zone);
          progressBar.remove();
          Utils.showToast('File uploaded successfully', 'success');
        } else {
          throw new Error('Upload failed');
        }
      } catch (error) {
        progressBar.remove();
        Utils.showToast('Upload failed', 'error');
      }
    },

    createProgressBar(filename) {
      const div = document.createElement('div');
      div.className = 'upload-progress';
      div.innerHTML = `
                <div class="upload-filename">${filename}</div>
                <div class="upload-bar">
                    <div class="upload-fill"></div>
                </div>
            `;
      return div;
    },

    showPreview(data, zone) {
      const preview = document.createElement('div');
      preview.className = 'file-preview';
      preview.innerHTML = `
                <img src="${data.url}" alt="${data.filename}">
                <button onclick="this.parentElement.remove()">×</button>
            `;
      zone.appendChild(preview);
    },

    setupReorder() {
      // Implement drag-to-reorder for lists
      const lists = document.querySelectorAll('.sortable-list');

      lists.forEach(list => {
        let draggedItem = null;

        list.addEventListener('dragstart', (e) => {
          draggedItem = e.target;
          e.target.classList.add('dragging');
        });

        list.addEventListener('dragend', (e) => {
          e.target.classList.remove('dragging');
        });

        list.addEventListener('dragover', (e) => {
          e.preventDefault();
          const afterElement = this.getDragAfterElement(list, e.clientY);
          if (afterElement == null) {
            list.appendChild(draggedItem);
          } else {
            list.insertBefore(draggedItem, afterElement);
          }
        });
      });
    },

    getDragAfterElement(container, y) {
      const draggableElements = [...container.querySelectorAll('.draggable:not(.dragging)')];

      return draggableElements.reduce((closest, child) => {
        const box = child.getBoundingClientRect();
        const offset = y - box.top - box.height / 2;

        if (offset < 0 && offset > closest.offset) {
          return { offset: offset, element: child };
        } else {
          return closest;
        }
      }, { offset: Number.NEGATIVE_INFINITY }).element;
    }
  },

  // ============================================
  // KEYBOARD SHORTCUTS
  // ============================================

  shortcuts: {
    init() {
      document.addEventListener('keydown', (e) => {
        // Ctrl+N: New item
        if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
          e.preventDefault();
          this.newItem();
        }

        // Ctrl+S: Save
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
          e.preventDefault();
          this.save();
        }

        // Esc: Close modal
        if (e.key === 'Escape') {
          Modals.closeAll();
        }
      });
    },

    newItem() {
      const addBtn = document.querySelector('[data-action="add"]');
      if (addBtn) addBtn.click();
    },

    save() {
      const saveBtn = document.querySelector('[data-action="save"]');
      if (saveBtn) saveBtn.click();
    }
  },

  // ============================================
  // INFINITE SCROLL
  // ============================================

  infiniteScroll: {
    loading: false,
    hasMore: true,
    currentPage: 1,

    init(container, loadFunction) {
      const observer = new IntersectionObserver((entries) => {
        if (entries[0].isIntersecting && !this.loading && this.hasMore) {
          this.loadMore(loadFunction);
        }
      }, { threshold: 0.1 });

      const sentinel = document.createElement('div');
      sentinel.className = 'scroll-sentinel';
      container.appendChild(sentinel);
      observer.observe(sentinel);
    },

    async loadMore(loadFunction) {
      this.loading = true;
      this.showLoader();

      try {
        const data = await loadFunction(this.currentPage + 1);
        if (data && data.results) {
          this.currentPage++;
          this.hasMore = !!data.next;
        }
      } catch (error) {
        console.error('Load more error:', error);
      } finally {
        this.loading = false;
        this.hideLoader();
      }
    },

    showLoader() {
      const loader = document.querySelector('.scroll-sentinel');
      if (loader) {
        loader.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i></div>';
      }
    },

    hideLoader() {
      const loader = document.querySelector('.scroll-sentinel');
      if (loader) loader.innerHTML = '';
    }
  },

  // ============================================
  // REAL-TIME UPDATES (WebSocket)
  // ============================================

  realtime: {
    socket: null,
    reconnectAttempts: 0,
    maxReconnectAttempts: 5,

    init() {
      this.connect();
    },

    connect() {
      const wsUrl = `ws://${window.location.host}/ws/admin/`;
      this.socket = new WebSocket(wsUrl);

      this.socket.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
      };

      this.socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        this.handleMessage(data);
      };

      this.socket.onclose = () => {
        console.log('WebSocket disconnected');
        this.reconnect();
      };

      this.socket.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    },

    handleMessage(data) {
      switch (data.type) {
        case 'notification':
          this.showNotification(data);
          break;
        case 'stats_update':
          this.updateStats(data);
          break;
        case 'viewer_count':
          this.updateViewerCount(data);
          break;
      }
    },

    reconnect() {
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts++;
        setTimeout(() => this.connect(), 1000 * this.reconnectAttempts);
      }
    },

    showNotification(data) {
      Utils.showToast(data.message, data.level || 'info');
    },

    updateStats(data) {
      Object.keys(data.stats).forEach(key => {
        const element = document.getElementById(key);
        if (element) element.textContent = data.stats[key];
      });
    },

    updateViewerCount(data) {
      const element = document.getElementById(`stream-${data.stream_id}-viewers`);
      if (element) element.textContent = data.count;
    }
  },

  // ============================================
  // INITIALIZATION
  // ============================================

  init() {
    this.search.init();
    this.bulkActions.init();
    this.dragDrop.init();
    this.shortcuts.init();
    // this.realtime.init(); // Uncomment when WebSocket is ready
  }
};

// Auto-initialize
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => AdvancedFeatures.init());
} else {
  AdvancedFeatures.init();
}

// Export
if (typeof module !== 'undefined' && module.exports) {
  module.exports = AdvancedFeatures;
}
