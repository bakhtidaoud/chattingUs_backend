/**
 * Moderation & Reports Management
 * Handle content moderation and user reports
 */

const ModerationManager = {
  currentPage: 1,
  perPage: 20,
  currentStatus: 'pending',
  filters: {
    search: '',
    type: 'all',
    priority: 'all',
    reporter: 'all'
  },

  /**
   * Initialize moderation management
   */
  init() {
    this.setupEventListeners();
    this.loadReports();
    this.loadStatistics();
  },

  /**
   * Setup event listeners
   */
  setupEventListeners() {
    // Status tabs
    document.querySelectorAll('.status-tab').forEach(tab => {
      tab.addEventListener('click', (e) => {
        const status = e.target.dataset.status;
        this.switchStatus(status);
      });
    });

    // Search
    const searchInput = document.getElementById('reportSearch');
    if (searchInput) {
      searchInput.addEventListener('input', Utils.debounce((e) => {
        this.filters.search = e.target.value;
        this.currentPage = 1;
        this.loadReports();
      }, 300));
    }

    // Filters
    ['reportTypeFilter', 'reportPriorityFilter', 'reportReporterFilter'].forEach(id => {
      const filter = document.getElementById(id);
      if (filter) {
        filter.addEventListener('change', (e) => {
          const filterName = id.replace('report', '').replace('Filter', '').toLowerCase();
          this.filters[filterName] = e.target.value;
          this.currentPage = 1;
          this.loadReports();
        });
      }
    });
  },

  /**
   * Switch status tab
   */
  switchStatus(status) {
    this.currentStatus = status;
    this.currentPage = 1;

    // Update active tab
    document.querySelectorAll('.status-tab').forEach(tab => {
      tab.classList.toggle('active', tab.dataset.status === status);
    });

    this.loadReports();
  },

  /**
   * Load reports
   */
  async loadReports() {
    const container = document.getElementById('reportsContainer');
    if (!container) return;

    container.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i><p>Loading reports...</p></div>';

    try {
      const params = {
        page: this.currentPage,
        page_size: this.perPage,
        status: this.currentStatus
      };

      if (this.filters.search) params.search = this.filters.search;
      if (this.filters.type !== 'all') params.type = this.filters.type;
      if (this.filters.priority !== 'all') params.priority = this.filters.priority;
      if (this.filters.reporter !== 'all') params.reporter = this.filters.reporter;

      const response = await API.get('/moderation/reports/', params);
      const reports = response.results || response;

      this.renderReports(reports);
      this.renderPagination(response);
    } catch (error) {
      console.error('Error loading reports:', error);
      container.innerHTML = '<p style="text-align: center; padding: 2rem;">Error loading reports</p>';
      Utils.showToast('Failed to load reports', 'error');
    }
  },

  /**
   * Render reports
   */
  renderReports(reports) {
    const container = document.getElementById('reportsContainer');
    if (!container) return;

    if (reports.length === 0) {
      container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-clipboard-check"></i>
                    <h3>No ${this.currentStatus} reports</h3>
                    <p>All clear! No reports to review in this category.</p>
                </div>
            `;
      return;
    }

    container.innerHTML = reports.map(report => {
      const typeInfo = this.getReportTypeInfo(report.type);
      const priorityInfo = this.getPriorityInfo(report.priority);

      return `
                <div class="report-card ${report.priority}" data-report-id="${report.id}">
                    <div class="report-header">
                        <div class="report-type-badge ${typeInfo.class}">
                            <i class="${typeInfo.icon}"></i>
                            ${typeInfo.label}
                        </div>
                        <div class="report-priority ${priorityInfo.class}">
                            <i class="fas fa-exclamation-circle"></i>
                            ${priorityInfo.label}
                        </div>
                        <span class="report-date">${Utils.formatDate(report.created_at)}</span>
                    </div>

                    <div class="report-body" onclick="ModerationManager.viewReport(${report.id})">
                        <div class="reporter-info">
                            <img src="${report.reporter?.profile_picture || `https://ui-avatars.com/api/?name=${encodeURIComponent(report.reporter?.username || 'Anonymous')}`}" 
                                 alt="${report.reporter?.username || 'Anonymous'}">
                            <div>
                                <h4>Reported by ${report.reporter?.username || 'Anonymous'}</h4>
                                <p class="report-target">Target: ${report.reported_user?.username || 'Content'}</p>
                            </div>
                        </div>

                        <div class="report-content-preview">
                            ${report.content_preview ? `
                                <div class="content-preview-box">
                                    ${report.content_type === 'image' ?
            `<img src="${report.content_preview}" alt="Reported content">` :
            `<p>${Utils.truncateText(report.content_preview, 150)}</p>`
          }
                                </div>
                            ` : ''}
                        </div>

                        <p class="report-description">${report.description || 'No description provided'}</p>
                    </div>

                    <div class="report-actions">
                        <button class="btn-icon" onclick="ModerationManager.viewReport(${report.id})" title="View Details">
                            <i class="fas fa-eye"></i>
                        </button>
                        ${this.currentStatus === 'pending' ? `
                            <button class="btn-icon btn-success" onclick="ModerationManager.quickApprove(${report.id})" title="Approve">
                                <i class="fas fa-check"></i>
                            </button>
                            <button class="btn-icon btn-danger" onclick="ModerationManager.quickRemove(${report.id})" title="Remove">
                                <i class="fas fa-trash"></i>
                            </button>
                        ` : ''}
                    </div>
                </div>
            `;
    }).join('');
  },

  /**
   * Get report type info
   */
  getReportTypeInfo(type) {
    const types = {
      spam: { icon: 'fas fa-ban', class: 'type-spam', label: 'Spam' },
      harassment: { icon: 'fas fa-user-slash', class: 'type-harassment', label: 'Harassment' },
      hate_speech: { icon: 'fas fa-angry', class: 'type-hate', label: 'Hate Speech' },
      violence: { icon: 'fas fa-fist-raised', class: 'type-violence', label: 'Violence' },
      nudity: { icon: 'fas fa-eye-slash', class: 'type-nudity', label: 'Nudity/Sexual' },
      false_info: { icon: 'fas fa-exclamation-triangle', class: 'type-false', label: 'False Info' },
      copyright: { icon: 'fas fa-copyright', class: 'type-copyright', label: 'Copyright' },
      other: { icon: 'fas fa-flag', class: 'type-other', label: 'Other' }
    };
    return types[type] || types.other;
  },

  /**
   * Get priority info
   */
  getPriorityInfo(priority) {
    const priorities = {
      low: { class: 'priority-low', label: 'Low' },
      medium: { class: 'priority-medium', label: 'Medium' },
      high: { class: 'priority-high', label: 'High' },
      urgent: { class: 'priority-urgent', label: 'Urgent' }
    };
    return priorities[priority] || priorities.medium;
  },

  /**
   * View report details
   */
  async viewReport(id) {
    Modals.open('reportDetailsModal');
    const body = document.getElementById('reportDetailsBody');
    body.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i></div>';

    try {
      const report = await API.get(`/moderation/reports/${id}/`);
      const typeInfo = this.getReportTypeInfo(report.type);
      const priorityInfo = this.getPriorityInfo(report.priority);

      body.innerHTML = `
                <div class="report-details-grid">
                    <div class="report-details-main">
                        <div class="report-details-header">
                            <div class="report-type-badge ${typeInfo.class}">
                                <i class="${typeInfo.icon}"></i>
                                ${typeInfo.label}
                            </div>
                            <div class="report-priority ${priorityInfo.class}">
                                <i class="fas fa-exclamation-circle"></i>
                                ${priorityInfo.label}
                            </div>
                        </div>

                        <div class="report-details-info">
                            <h3>Report Details</h3>
                            <div class="info-row">
                                <span class="info-label">Reporter:</span>
                                <span class="info-value">${report.reporter?.username || 'Anonymous'}</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">Reported User:</span>
                                <span class="info-value">${report.reported_user?.username || 'N/A'}</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">Created:</span>
                                <span class="info-value">${Utils.formatDate(report.created_at)}</span>
                            </div>
                            <div class="info-row">
                                <span class="info-label">Status:</span>
                                <span class="info-value"><span class="status-badge ${report.status}">${report.status}</span></span>
                            </div>
                        </div>

                        <div class="report-details-content">
                            <h4>Reported Content</h4>
                            ${report.content_url ? `
                                <div class="content-full-view">
                                    ${report.content_type === 'image' ?
            `<img src="${report.content_url}" alt="Reported content">` :
            report.content_type === 'video' ?
              `<video src="${report.content_url}" controls></video>` :
              `<p>${report.content_text || 'Content not available'}</p>`
          }
                                </div>
                            ` : '<p>Content not available</p>'}
                        </div>

                        <div class="report-details-description">
                            <h4>Description</h4>
                            <p>${report.description || 'No description provided'}</p>
                        </div>

                        ${report.similar_reports && report.similar_reports.length > 0 ? `
                            <div class="similar-reports">
                                <h4>Similar Reports (${report.similar_reports.length})</h4>
                                <div class="similar-reports-list">
                                    ${report.similar_reports.map(sr => `
                                        <div class="similar-report-item">
                                            <span>${sr.reporter?.username || 'Anonymous'}</span>
                                            <span>${Utils.formatDate(sr.created_at)}</span>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        ` : ''}

                        <div class="admin-notes">
                            <h4>Admin Notes</h4>
                            <textarea id="adminNotes" rows="4" placeholder="Add notes about this report...">${report.admin_notes || ''}</textarea>
                            <button class="btn-secondary btn-sm" onclick="ModerationManager.saveNotes(${report.id})">
                                Save Notes
                            </button>
                        </div>
                    </div>

                    <div class="report-details-sidebar">
                        <h4>Moderation Actions</h4>
                        <div class="moderation-actions-list">
                            <button class="moderation-action-btn approve" onclick="ModerationManager.approveContent(${report.id})">
                                <i class="fas fa-check-circle"></i>
                                Approve Content
                            </button>
                            <button class="moderation-action-btn remove" onclick="ModerationManager.removeContent(${report.id})">
                                <i class="fas fa-trash-alt"></i>
                                Remove Content
                            </button>
                            <button class="moderation-action-btn ban" onclick="ModerationManager.banUser(${report.id})">
                                <i class="fas fa-ban"></i>
                                Ban User
                            </button>
                            <button class="moderation-action-btn warn" onclick="ModerationManager.warnUser(${report.id})">
                                <i class="fas fa-exclamation-triangle"></i>
                                Warn User
                            </button>
                            <button class="moderation-action-btn dismiss" onclick="ModerationManager.dismissReport(${report.id})">
                                <i class="fas fa-times-circle"></i>
                                Dismiss Report
                            </button>
                            <button class="moderation-action-btn escalate" onclick="ModerationManager.escalateReport(${report.id})">
                                <i class="fas fa-arrow-up"></i>
                                Escalate
                            </button>
                        </div>

                        ${report.action_history && report.action_history.length > 0 ? `
                            <div class="action-history">
                                <h4>Action History</h4>
                                <div class="timeline">
                                    ${report.action_history.map(action => `
                                        <div class="timeline-item">
                                            <div class="timeline-marker"></div>
                                            <div class="timeline-content">
                                                <h5>${action.action_type}</h5>
                                                <p>By ${action.moderator?.username || 'System'}</p>
                                                <span>${Utils.formatDate(action.created_at)}</span>
                                            </div>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        ` : ''}
                    </div>
                </div>
            `;
    } catch (error) {
      console.error('Error loading report:', error);
      body.innerHTML = '<p style="text-align: center; color: #ef4444;">Error loading report details</p>';
    }
  },

  /**
   * Quick approve
   */
  async quickApprove(id) {
    if (!confirm('Approve this content and dismiss the report?')) return;

    try {
      await this.approveContent(id);
    } catch (error) {
      console.error('Error approving:', error);
    }
  },

  /**
   * Quick remove
   */
  async quickRemove(id) {
    if (!confirm('Remove this content and resolve the report?')) return;

    try {
      await this.removeContent(id);
    } catch (error) {
      console.error('Error removing:', error);
    }
  },

  /**
   * Approve content
   */
  async approveContent(reportId) {
    try {
      await API.post('/moderation/actions/', {
        report_id: reportId,
        action_type: 'approve_content',
        reason: 'Content approved after review'
      });

      await API.put(`/moderation/reports/${reportId}/`, { status: 'resolved' });

      Utils.showToast('Content approved successfully', 'success');
      Modals.close('reportDetailsModal');
      this.loadReports();
      this.loadStatistics();
    } catch (error) {
      console.error('Error approving content:', error);
      Utils.showToast('Failed to approve content', 'error');
    }
  },

  /**
   * Remove content
   */
  async removeContent(reportId) {
    const reason = prompt('Reason for removing content:');
    if (!reason) return;

    try {
      await API.post('/moderation/actions/', {
        report_id: reportId,
        action_type: 'remove_content',
        reason: reason
      });

      await API.put(`/moderation/reports/${reportId}/`, { status: 'resolved' });

      Utils.showToast('Content removed successfully', 'success');
      Modals.close('reportDetailsModal');
      this.loadReports();
      this.loadStatistics();
    } catch (error) {
      console.error('Error removing content:', error);
      Utils.showToast('Failed to remove content', 'error');
    }
  },

  /**
   * Ban user
   */
  async banUser(reportId) {
    const reason = prompt('Reason for banning user:');
    if (!reason) return;

    if (!confirm('Are you sure you want to ban this user?')) return;

    try {
      await API.post('/moderation/actions/', {
        report_id: reportId,
        action_type: 'ban_user',
        reason: reason
      });

      await API.put(`/moderation/reports/${reportId}/`, { status: 'resolved' });

      Utils.showToast('User banned successfully', 'success');
      Modals.close('reportDetailsModal');
      this.loadReports();
      this.loadStatistics();
    } catch (error) {
      console.error('Error banning user:', error);
      Utils.showToast('Failed to ban user', 'error');
    }
  },

  /**
   * Warn user
   */
  async warnUser(reportId) {
    const reason = prompt('Warning message:');
    if (!reason) return;

    try {
      await API.post('/moderation/actions/', {
        report_id: reportId,
        action_type: 'warn_user',
        reason: reason
      });

      Utils.showToast('Warning sent to user', 'success');
      this.loadReports();
    } catch (error) {
      console.error('Error warning user:', error);
      Utils.showToast('Failed to send warning', 'error');
    }
  },

  /**
   * Dismiss report
   */
  async dismissReport(reportId) {
    const reason = prompt('Reason for dismissing:');
    if (!reason) return;

    try {
      await API.post('/moderation/actions/', {
        report_id: reportId,
        action_type: 'dismiss_report',
        reason: reason
      });

      await API.put(`/moderation/reports/${reportId}/`, { status: 'dismissed' });

      Utils.showToast('Report dismissed', 'success');
      Modals.close('reportDetailsModal');
      this.loadReports();
      this.loadStatistics();
    } catch (error) {
      console.error('Error dismissing report:', error);
      Utils.showToast('Failed to dismiss report', 'error');
    }
  },

  /**
   * Escalate report
   */
  async escalateReport(reportId) {
    try {
      await API.post('/moderation/actions/', {
        report_id: reportId,
        action_type: 'escalate',
        reason: 'Escalated for senior review'
      });

      await API.put(`/moderation/reports/${reportId}/`, {
        priority: 'urgent',
        status: 'reviewing'
      });

      Utils.showToast('Report escalated', 'success');
      Modals.close('reportDetailsModal');
      this.loadReports();
      this.loadStatistics();
    } catch (error) {
      console.error('Error escalating report:', error);
      Utils.showToast('Failed to escalate report', 'error');
    }
  },

  /**
   * Save admin notes
   */
  async saveNotes(reportId) {
    const notes = document.getElementById('adminNotes').value;

    try {
      await API.put(`/moderation/reports/${reportId}/`, { admin_notes: notes });
      Utils.showToast('Notes saved', 'success');
    } catch (error) {
      console.error('Error saving notes:', error);
      Utils.showToast('Failed to save notes', 'error');
    }
  },

  /**
   * Load statistics
   */
  async loadStatistics() {
    try {
      const stats = await API.get('/moderation/reports/statistics/');

      const totalEl = document.getElementById('totalReports');
      if (totalEl) totalEl.textContent = stats.total || 0;

      const pendingEl = document.getElementById('pendingReports');
      if (pendingEl) pendingEl.textContent = stats.pending || 0;

      const avgTimeEl = document.getElementById('avgResolutionTime');
      if (avgTimeEl) avgTimeEl.textContent = stats.avg_resolution_time || 'N/A';

      // Update tab counts
      document.querySelectorAll('.status-tab').forEach(tab => {
        const status = tab.dataset.status;
        const count = stats[`${status}_count`] || 0;
        const badge = tab.querySelector('.tab-badge');
        if (badge) badge.textContent = count;
      });
    } catch (error) {
      console.error('Error loading statistics:', error);
    }
  },

  /**
   * Render pagination
   */
  renderPagination(response) {
    const pagination = document.getElementById('reportsPagination');
    if (!pagination || !response.count) return;

    const totalPages = Math.ceil(response.count / this.perPage);
    if (totalPages <= 1) {
      pagination.innerHTML = '';
      return;
    }

    let html = '<div class="pagination">';

    html += `<button class="pagination-btn" ${this.currentPage === 1 ? 'disabled' : ''} 
                 onclick="ModerationManager.goToPage(${this.currentPage - 1})">
                 <i class="fas fa-chevron-left"></i>
                 </button>`;

    for (let i = 1; i <= Math.min(totalPages, 5); i++) {
      html += `<button class="pagination-btn ${i === this.currentPage ? 'active' : ''}" 
                     onclick="ModerationManager.goToPage(${i})">${i}</button>`;
    }

    html += `<button class="pagination-btn" ${this.currentPage === totalPages ? 'disabled' : ''} 
                 onclick="ModerationManager.goToPage(${this.currentPage + 1})">
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
    this.loadReports();
  }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ModerationManager;
}
