/**
 * Notifications Management
 * Manage and monitor all system notifications
 */

const NotificationsManager = {
  currentPage: 1,
  perPage: 20,
  filters: {
    search: '',
    type: 'all',
    status: 'all',
    recipient: 'all'
  },
  selectedNotifications: new Set(),

  /**
   * Initialize notifications management
   */
  init() {
    this.setupEventListeners();
    this.loadNotifications();
    this.loadStatistics();
  },

  /**
   * Setup event listeners
   */
  setupEventListeners() {
    // Search
    const searchInput = document.getElementById('notificationSearch');
    if (searchInput) {
      searchInput.addEventListener('input', Utils.debounce((e) => {
        this.filters.search = e.target.value;
        this.currentPage = 1;
        this.loadNotifications();
      }, 300));
    }

    // Filters
    ['notificationTypeFilter', 'notificationStatusFilter', 'notificationRecipientFilter'].forEach(id => {
      const filter = document.getElementById(id);
      if (filter) {
        filter.addEventListener('change', (e) => {
          const filterName = id.replace('notification', '').replace('Filter', '').toLowerCase();
          this.filters[filterName] = e.target.value;
          this.currentPage = 1;
          this.loadNotifications();
        });
      }
    });

    // Select all checkbox
    const selectAll = document.getElementById('selectAllNotifications');
    if (selectAll) {
      selectAll.addEventListener('change', (e) => {
        this.toggleSelectAll(e.target.checked);
      });
    }

    // Bulk actions
    const bulkMarkReadBtn = document.getElementById('bulkMarkReadBtn');
    if (bulkMarkReadBtn) {
      bulkMarkReadBtn.addEventListener('click', () => this.handleBulkMarkRead());
    }

    const bulkDeleteBtn = document.getElementById('bulkDeleteNotificationsBtn');
    if (bulkDeleteBtn) {
      bulkDeleteBtn.addEventListener('click', () => this.handleBulkDelete());
    }

    const clearSelectionBtn = document.getElementById('clearNotificationSelectionBtn');
    if (clearSelectionBtn) {
      clearSelectionBtn.addEventListener('click', () => this.clearSelection());
    }
  },

  /**
   * Load notifications
   */
  async loadNotifications() {
    const container = document.getElementById('notificationsContainer');
    if (!container) return;

    container.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i><p>Loading notifications...</p></div>';

    try {
      const params = {
        page: this.currentPage,
        page_size: this.perPage
      };

      if (this.filters.search) params.search = this.filters.search;
      if (this.filters.type !== 'all') params.type = this.filters.type;
      if (this.filters.status !== 'all') params.is_read = this.filters.status === 'read';
      if (this.filters.recipient !== 'all') params.recipient = this.filters.recipient;

      const response = await API.get('/notifications/', params);
      const notifications = response.results || response;

      this.renderNotifications(notifications);
      this.renderPagination(response);
    } catch (error) {
      console.error('Error loading notifications:', error);
      container.innerHTML = '<p style="text-align: center; padding: 2rem;">Error loading notifications</p>';
      Utils.showToast('Failed to load notifications', 'error');
    }
  },

  /**
   * Render notifications
   */
  renderNotifications(notifications) {
    const container = document.getElementById('notificationsContainer');
    if (!container) return;

    if (notifications.length === 0) {
      container.innerHTML = '<p style="text-align: center; padding: 2rem;">No notifications found</p>';
      return;
    }

    container.innerHTML = notifications.map(notification => {
      const typeInfo = this.getNotificationTypeInfo(notification.type);
      const isUnread = !notification.is_read;

      return `
                <div class="notification-card ${isUnread ? 'unread' : ''}" data-notification-id="${notification.id}">
                    <div class="notification-checkbox">
                        <input type="checkbox" class="notification-checkbox-input" data-notification-id="${notification.id}" 
                               ${this.selectedNotifications.has(notification.id) ? 'checked' : ''}>
                    </div>
                    <div class="notification-icon ${typeInfo.class}">
                        <i class="${typeInfo.icon}"></i>
                    </div>
                    <div class="notification-content" onclick="NotificationsManager.viewNotification(${notification.id})">
                        <div class="notification-header">
                            <img src="${notification.sender?.profile_picture || `https://ui-avatars.com/api/?name=${encodeURIComponent(notification.sender?.username || 'System')}`}" 
                                 alt="${notification.sender?.username || 'System'}"
                                 class="notification-avatar">
                            <div class="notification-meta">
                                <h4>${notification.sender?.username || 'System'}</h4>
                                <p class="notification-text">${notification.message}</p>
                            </div>
                            ${isUnread ? '<span class="unread-indicator"></span>' : ''}
                        </div>
                        <div class="notification-footer">
                            <span class="notification-time">${Utils.formatDate(notification.created_at)}</span>
                            <span class="notification-type-badge">${typeInfo.label}</span>
                        </div>
                    </div>
                    <div class="notification-actions">
                        ${isUnread ?
          `<button class="btn-icon" onclick="NotificationsManager.markAsRead(${notification.id})" title="Mark as Read">
                                <i class="fas fa-check"></i>
                            </button>` :
          `<button class="btn-icon" onclick="NotificationsManager.markAsUnread(${notification.id})" title="Mark as Unread">
                                <i class="fas fa-envelope"></i>
                            </button>`
        }
                        ${notification.related_object_url ?
          `<button class="btn-icon" onclick="NotificationsManager.viewRelated('${notification.related_object_url}')" title="View Related">
                                <i class="fas fa-external-link-alt"></i>
                            </button>` : ''
        }
                        <button class="btn-icon btn-danger" onclick="NotificationsManager.deleteNotification(${notification.id})" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `;
    }).join('');

    // Add checkbox listeners
    document.querySelectorAll('.notification-checkbox-input').forEach(checkbox => {
      checkbox.addEventListener('change', (e) => {
        e.stopPropagation();
        const notificationId = parseInt(e.target.dataset.notificationId);
        if (e.target.checked) {
          this.selectedNotifications.add(notificationId);
        } else {
          this.selectedNotifications.delete(notificationId);
        }
        this.updateBulkActions();
      });
    });
  },

  /**
   * Get notification type info
   */
  getNotificationTypeInfo(type) {
    const types = {
      like: {
        icon: 'fas fa-heart',
        class: 'type-like',
        label: 'Like'
      },
      comment: {
        icon: 'fas fa-comment',
        class: 'type-comment',
        label: 'Comment'
      },
      follow: {
        icon: 'fas fa-user-plus',
        class: 'type-follow',
        label: 'Follow'
      },
      message: {
        icon: 'fas fa-envelope',
        class: 'type-message',
        label: 'Message'
      },
      mention: {
        icon: 'fas fa-at',
        class: 'type-mention',
        label: 'Mention'
      },
      system: {
        icon: 'fas fa-bell',
        class: 'type-system',
        label: 'System'
      }
    };
    return types[type] || types.system;
  },

  /**
   * View notification
   */
  async viewNotification(id) {
    try {
      // Mark as read
      await this.markAsRead(id);

      // Get notification details
      const notification = await API.get(`/notifications/${id}/`);

      // If there's a related URL, navigate to it
      if (notification.related_object_url) {
        this.viewRelated(notification.related_object_url);
      }
    } catch (error) {
      console.error('Error viewing notification:', error);
    }
  },

  /**
   * View related content
   */
  viewRelated(url) {
    // Open in new tab or navigate
    window.open(url, '_blank');
  },

  /**
   * Mark as read
   */
  async markAsRead(id) {
    try {
      await API.put(`/notifications/${id}/mark-read/`, { is_read: true });
      this.loadNotifications();
      this.loadStatistics();
    } catch (error) {
      console.error('Error marking as read:', error);
      Utils.showToast('Failed to mark as read', 'error');
    }
  },

  /**
   * Mark as unread
   */
  async markAsUnread(id) {
    try {
      await API.put(`/notifications/${id}/mark-read/`, { is_read: false });
      this.loadNotifications();
      this.loadStatistics();
    } catch (error) {
      console.error('Error marking as unread:', error);
      Utils.showToast('Failed to mark as unread', 'error');
    }
  },

  /**
   * Delete notification
   */
  async deleteNotification(id) {
    if (!confirm('Are you sure you want to delete this notification?')) return;

    try {
      await API.delete(`/notifications/${id}/`);
      Utils.showToast('Notification deleted successfully', 'success');
      this.loadNotifications();
      this.loadStatistics();
    } catch (error) {
      console.error('Error deleting notification:', error);
      Utils.showToast('Failed to delete notification', 'error');
    }
  },

  /**
   * Toggle select all
   */
  toggleSelectAll(checked) {
    document.querySelectorAll('.notification-checkbox-input').forEach(checkbox => {
      checkbox.checked = checked;
      const notificationId = parseInt(checkbox.dataset.notificationId);
      if (checked) {
        this.selectedNotifications.add(notificationId);
      } else {
        this.selectedNotifications.delete(notificationId);
      }
    });
    this.updateBulkActions();
  },

  /**
   * Update bulk actions visibility
   */
  updateBulkActions() {
    const bulkActions = document.getElementById('notificationBulkActions');
    const selectedCount = document.getElementById('selectedNotificationsCount');

    if (this.selectedNotifications.size > 0) {
      if (bulkActions) bulkActions.style.display = 'flex';
      if (selectedCount) selectedCount.textContent = this.selectedNotifications.size;
    } else {
      if (bulkActions) bulkActions.style.display = 'none';
    }
  },

  /**
   * Clear selection
   */
  clearSelection() {
    this.selectedNotifications.clear();
    document.querySelectorAll('.notification-checkbox-input').forEach(cb => cb.checked = false);
    document.getElementById('selectAllNotifications').checked = false;
    this.updateBulkActions();
  },

  /**
   * Handle bulk mark as read
   */
  async handleBulkMarkRead() {
    if (!confirm(`Are you sure you want to mark ${this.selectedNotifications.size} notifications as read?`)) return;

    try {
      await Promise.all(
        Array.from(this.selectedNotifications).map(id =>
          API.put(`/notifications/${id}/mark-read/`, { is_read: true })
        )
      );
      Utils.showToast(`${this.selectedNotifications.size} notifications marked as read`, 'success');
      this.clearSelection();
      this.loadNotifications();
      this.loadStatistics();
    } catch (error) {
      console.error('Error marking notifications as read:', error);
      Utils.showToast('Failed to mark some notifications as read', 'error');
    }
  },

  /**
   * Handle bulk delete
   */
  async handleBulkDelete() {
    if (!confirm(`Are you sure you want to delete ${this.selectedNotifications.size} notifications?`)) return;

    try {
      await Promise.all(
        Array.from(this.selectedNotifications).map(id => API.delete(`/notifications/${id}/`))
      );
      Utils.showToast(`${this.selectedNotifications.size} notifications deleted successfully`, 'success');
      this.clearSelection();
      this.loadNotifications();
      this.loadStatistics();
    } catch (error) {
      console.error('Error deleting notifications:', error);
      Utils.showToast('Failed to delete some notifications', 'error');
    }
  },

  /**
   * Load statistics
   */
  async loadStatistics() {
    try {
      const stats = await API.get('/notifications/statistics/');

      // Update stat cards
      const totalEl = document.getElementById('totalNotifications');
      if (totalEl) totalEl.textContent = stats.total || 0;

      const unreadEl = document.getElementById('unreadNotifications');
      if (unreadEl) unreadEl.textContent = stats.unread || 0;

      const readRateEl = document.getElementById('readRate');
      if (readRateEl) {
        const rate = stats.total > 0 ? ((stats.read / stats.total) * 100).toFixed(1) : 0;
        readRateEl.textContent = `${rate}%`;
      }

      const clickRateEl = document.getElementById('clickRate');
      if (clickRateEl) {
        const rate = stats.total > 0 ? ((stats.clicked / stats.total) * 100).toFixed(1) : 0;
        clickRateEl.textContent = `${rate}%`;
      }
    } catch (error) {
      console.error('Error loading statistics:', error);
    }
  },

  /**
   * View user preferences
   */
  async viewPreferences(userId) {
    Modals.open('notificationPreferencesModal');
    const body = document.getElementById('preferencesBody');
    body.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i></div>';

    try {
      const preferences = await API.get(`/notifications/preferences/${userId}/`);

      body.innerHTML = `
                <form id="preferencesForm">
                    <div class="preferences-section">
                        <h4>Push Notifications</h4>
                        <div class="preference-item">
                            <label>
                                <input type="checkbox" name="push_likes" ${preferences.push_likes ? 'checked' : ''}>
                                Likes
                            </label>
                        </div>
                        <div class="preference-item">
                            <label>
                                <input type="checkbox" name="push_comments" ${preferences.push_comments ? 'checked' : ''}>
                                Comments
                            </label>
                        </div>
                        <div class="preference-item">
                            <label>
                                <input type="checkbox" name="push_follows" ${preferences.push_follows ? 'checked' : ''}>
                                Follows
                            </label>
                        </div>
                        <div class="preference-item">
                            <label>
                                <input type="checkbox" name="push_messages" ${preferences.push_messages ? 'checked' : ''}>
                                Messages
                            </label>
                        </div>
                    </div>

                    <div class="preferences-section">
                        <h4>Email Notifications</h4>
                        <div class="preference-item">
                            <label>
                                <input type="checkbox" name="email_likes" ${preferences.email_likes ? 'checked' : ''}>
                                Likes
                            </label>
                        </div>
                        <div class="preference-item">
                            <label>
                                <input type="checkbox" name="email_comments" ${preferences.email_comments ? 'checked' : ''}>
                                Comments
                            </label>
                        </div>
                        <div class="preference-item">
                            <label>
                                <input type="checkbox" name="email_follows" ${preferences.email_follows ? 'checked' : ''}>
                                Follows
                            </label>
                        </div>
                    </div>

                    <div class="preferences-section">
                        <h4>In-App Notifications</h4>
                        <div class="preference-item">
                            <label>
                                <input type="checkbox" name="inapp_likes" ${preferences.inapp_likes ? 'checked' : ''}>
                                Likes
                            </label>
                        </div>
                        <div class="preference-item">
                            <label>
                                <input type="checkbox" name="inapp_comments" ${preferences.inapp_comments ? 'checked' : ''}>
                                Comments
                            </label>
                        </div>
                        <div class="preference-item">
                            <label>
                                <input type="checkbox" name="inapp_follows" ${preferences.inapp_follows ? 'checked' : ''}>
                                Follows
                            </label>
                        </div>
                        <div class="preference-item">
                            <label>
                                <input type="checkbox" name="inapp_messages" ${preferences.inapp_messages ? 'checked' : ''}>
                                Messages
                            </label>
                        </div>
                    </div>

                    <div class="modal-footer">
                        <button type="button" class="btn-secondary" data-modal="notificationPreferencesModal">Cancel</button>
                        <button type="submit" class="btn-primary">Save Preferences</button>
                    </div>
                </form>
            `;

      // Handle form submission
      document.getElementById('preferencesForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await this.savePreferences(userId, new FormData(e.target));
      });
    } catch (error) {
      console.error('Error loading preferences:', error);
      body.innerHTML = '<p style="text-align: center; color: #ef4444;">Error loading preferences</p>';
    }
  },

  /**
   * Save preferences
   */
  async savePreferences(userId, formData) {
    try {
      const preferences = {};
      for (let [key, value] of formData.entries()) {
        preferences[key] = value === 'on';
      }

      await API.put(`/notifications/preferences/${userId}/`, preferences);
      Utils.showToast('Preferences saved successfully', 'success');
      Modals.close('notificationPreferencesModal');
    } catch (error) {
      console.error('Error saving preferences:', error);
      Utils.showToast('Failed to save preferences', 'error');
    }
  },

  /**
   * Render pagination
   */
  renderPagination(response) {
    const pagination = document.getElementById('notificationsPagination');
    if (!pagination || !response.count) return;

    const totalPages = Math.ceil(response.count / this.perPage);
    if (totalPages <= 1) {
      pagination.innerHTML = '';
      return;
    }

    let html = '<div class="pagination">';

    html += `<button class="pagination-btn" ${this.currentPage === 1 ? 'disabled' : ''} 
                 onclick="NotificationsManager.goToPage(${this.currentPage - 1})">
                 <i class="fas fa-chevron-left"></i>
                 </button>`;

    for (let i = 1; i <= Math.min(totalPages, 5); i++) {
      html += `<button class="pagination-btn ${i === this.currentPage ? 'active' : ''}" 
                     onclick="NotificationsManager.goToPage(${i})">${i}</button>`;
    }

    html += `<button class="pagination-btn" ${this.currentPage === totalPages ? 'disabled' : ''} 
                 onclick="NotificationsManager.goToPage(${this.currentPage + 1})">
                 <i class="fas fa-chevron-right"></i>
                 </button>`;

    html += '</div>';
    pagination.innerHTML = html;
  },

  /**
   * Go to page
   */
  goToPage(page) {
    this.currentPage = page;
    this.loadNotifications();
  }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
  module.exports = NotificationsManager;
}
