/**
 * Security Management
 * Monitor and manage security features
 */

const SecurityManager = {
  currentView: 'overview',
  currentPage: 1,
  perPage: 20,

  /**
   * Initialize security management
   */
  init() {
    this.setupEventListeners();
    this.loadOverview();
  },

  /**
   * Setup event listeners
   */
  setupEventListeners() {
    // View tabs
    document.querySelectorAll('.security-tab').forEach(tab => {
      tab.addEventListener('click', (e) => {
        const view = e.target.dataset.view;
        this.switchView(view);
      });
    });

    // Add IP to blacklist
    const addIpBtn = document.getElementById('addIpBtn');
    if (addIpBtn) {
      addIpBtn.addEventListener('click', () => {
        Modals.open('addIpModal');
      });
    }

    // Add IP form
    const addIpForm = document.getElementById('addIpForm');
    if (addIpForm) {
      addIpForm.addEventListener('submit', (e) => {
        e.preventDefault();
        this.handleAddIp();
      });
    }
  },

  /**
   * Switch view
   */
  switchView(view) {
    this.currentView = view;
    this.currentPage = 1;

    // Update active tab
    document.querySelectorAll('.security-tab').forEach(tab => {
      tab.classList.toggle('active', tab.dataset.view === view);
    });

    // Hide all views
    document.querySelectorAll('.security-view').forEach(v => {
      v.style.display = 'none';
    });

    // Show selected view
    const selectedView = document.getElementById(`${view}View`);
    if (selectedView) {
      selectedView.style.display = 'block';
    }

    // Load data for view
    switch (view) {
      case 'overview':
        this.loadOverview();
        break;
      case '2fa':
        this.load2FAUsers();
        break;
      case 'failed-logins':
        this.loadFailedLogins();
        break;
      case 'sessions':
        this.loadActiveSessions();
        break;
      case 'logs':
        this.loadSecurityLogs();
        break;
      case 'blacklist':
        this.loadBlacklist();
        break;
    }
  },

  /**
   * Load security overview
   */
  async loadOverview() {
    try {
      const overview = await API.get('/security/overview/');

      // Update stats cards
      const users2faEl = document.getElementById('users2faCount');
      if (users2faEl) users2faEl.textContent = overview.users_with_2fa || 0;

      const failedLoginsEl = document.getElementById('failedLoginsCount');
      if (failedLoginsEl) failedLoginsEl.textContent = overview.failed_logins_24h || 0;

      const suspiciousEl = document.getElementById('suspiciousCount');
      if (suspiciousEl) suspiciousEl.textContent = overview.suspicious_activities || 0;

      const blockedIpsEl = document.getElementById('blockedIpsCount');
      if (blockedIpsEl) blockedIpsEl.textContent = overview.blocked_ips || 0;

      const activeSessionsEl = document.getElementById('activeSessionsCount');
      if (activeSessionsEl) activeSessionsEl.textContent = overview.active_sessions || 0;

      // Show alerts if needed
      this.showSecurityAlerts(overview);
    } catch (error) {
      console.error('Error loading overview:', error);
      Utils.showToast('Failed to load security overview', 'error');
    }
  },

  /**
   * Show security alerts
   */
  showSecurityAlerts(overview) {
    const alertsContainer = document.getElementById('securityAlerts');
    if (!alertsContainer) return;

    const alerts = [];

    if (overview.failed_logins_24h > 50) {
      alerts.push({
        type: 'danger',
        icon: 'fas fa-exclamation-triangle',
        message: `High number of failed login attempts: ${overview.failed_logins_24h} in last 24 hours`
      });
    }

    if (overview.suspicious_activities > 10) {
      alerts.push({
        type: 'warning',
        icon: 'fas fa-shield-alt',
        message: `${overview.suspicious_activities} suspicious activities detected`
      });
    }

    if (alerts.length === 0) {
      alertsContainer.innerHTML = '<div class="alert-success"><i class="fas fa-check-circle"></i> All security metrics are normal</div>';
      return;
    }

    alertsContainer.innerHTML = alerts.map(alert => `
            <div class="alert-${alert.type}">
                <i class="${alert.icon}"></i>
                ${alert.message}
            </div>
        `).join('');
  },

  /**
   * Load 2FA users
   */
  async load2FAUsers() {
    const container = document.getElementById('2faUsersContainer');
    if (!container) return;

    container.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i></div>';

    try {
      const users = await API.get('/security/2fa/users/');

      if (users.length === 0) {
        container.innerHTML = '<p style="text-align: center; padding: 2rem;">No users found</p>';
        return;
      }

      container.innerHTML = `
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>User</th>
                            <th>Email</th>
                            <th>2FA Status</th>
                            <th>Enabled Date</th>
                            <th>Backup Codes</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${users.map(user => `
                            <tr>
                                <td>
                                    <div class="user-cell">
                                        <img src="${user.profile_picture || `https://ui-avatars.com/api/?name=${encodeURIComponent(user.username)}`}" alt="${user.username}">
                                        <span>${user.username}</span>
                                    </div>
                                </td>
                                <td>${user.email}</td>
                                <td>
                                    <span class="status-badge ${user.has_2fa ? 'enabled' : 'disabled'}">
                                        ${user.has_2fa ? 'Enabled' : 'Disabled'}
                                    </span>
                                </td>
                                <td>${user.twofa_enabled_at ? Utils.formatDate(user.twofa_enabled_at) : 'N/A'}</td>
                                <td>${user.backup_codes_count || 0} remaining</td>
                                <td>
                                    ${user.has_2fa ? `
                                        <button class="btn-icon btn-danger" onclick="SecurityManager.reset2FA(${user.id})" title="Reset 2FA">
                                            <i class="fas fa-redo"></i>
                                        </button>
                                    ` : ''}
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
    } catch (error) {
      console.error('Error loading 2FA users:', error);
      container.innerHTML = '<p style="text-align: center; color: #ef4444;">Error loading users</p>';
    }
  },

  /**
   * Reset 2FA for user
   */
  async reset2FA(userId) {
    if (!confirm('Are you sure you want to reset 2FA for this user? They will need to set it up again.')) return;

    try {
      await API.post(`/security/2fa/${userId}/reset/`, {});
      Utils.showToast('2FA reset successfully', 'success');
      this.load2FAUsers();
    } catch (error) {
      console.error('Error resetting 2FA:', error);
      Utils.showToast('Failed to reset 2FA', 'error');
    }
  },

  /**
   * Load failed logins
   */
  async loadFailedLogins() {
    const container = document.getElementById('failedLoginsContainer');
    if (!container) return;

    container.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i></div>';

    try {
      const attempts = await API.get('/security/failed-logins/');

      if (attempts.length === 0) {
        container.innerHTML = '<p style="text-align: center; padding: 2rem;">No failed login attempts</p>';
        return;
      }

      container.innerHTML = `
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>User/Email</th>
                            <th>IP Address</th>
                            <th>Location</th>
                            <th>Reason</th>
                            <th>Timestamp</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${attempts.map(attempt => `
                            <tr>
                                <td>${attempt.username || attempt.email || 'Unknown'}</td>
                                <td><code>${attempt.ip_address}</code></td>
                                <td>${attempt.location || 'Unknown'}</td>
                                <td>
                                    <span class="reason-badge ${attempt.reason}">
                                        ${this.getFailureReason(attempt.reason)}
                                    </span>
                                </td>
                                <td>${Utils.formatDate(attempt.timestamp)}</td>
                                <td>
                                    <button class="btn-icon btn-danger" onclick="SecurityManager.blockIP('${attempt.ip_address}')" title="Block IP">
                                        <i class="fas fa-ban"></i>
                                    </button>
                                    ${attempt.user_id ? `
                                        <button class="btn-icon btn-warning" onclick="SecurityManager.lockAccount(${attempt.user_id})" title="Lock Account">
                                            <i class="fas fa-lock"></i>
                                        </button>
                                    ` : ''}
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
    } catch (error) {
      console.error('Error loading failed logins:', error);
      container.innerHTML = '<p style="text-align: center; color: #ef4444;">Error loading failed logins</p>';
    }
  },

  /**
   * Get failure reason label
   */
  getFailureReason(reason) {
    const reasons = {
      invalid_password: 'Invalid Password',
      invalid_username: 'Invalid Username',
      account_locked: 'Account Locked',
      account_disabled: 'Account Disabled',
      too_many_attempts: 'Too Many Attempts'
    };
    return reasons[reason] || reason;
  },

  /**
   * Load active sessions
   */
  async loadActiveSessions() {
    const container = document.getElementById('sessionsContainer');
    if (!container) return;

    container.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i></div>';

    try {
      const sessions = await API.get('/security/sessions/');

      if (sessions.length === 0) {
        container.innerHTML = '<p style="text-align: center; padding: 2rem;">No active sessions</p>';
        return;
      }

      container.innerHTML = sessions.map(session => `
                <div class="session-card">
                    <div class="session-header">
                        <div class="session-user">
                            <img src="${session.user?.profile_picture || `https://ui-avatars.com/api/?name=${encodeURIComponent(session.user?.username || 'User')}`}" 
                                 alt="${session.user?.username}">
                            <div>
                                <h4>${session.user?.username || 'Unknown'}</h4>
                                <p>${session.user?.email || ''}</p>
                            </div>
                        </div>
                        ${session.is_current ? '<span class="current-badge">Current Session</span>' : ''}
                    </div>
                    <div class="session-details">
                        <div class="session-info">
                            <i class="fas fa-laptop"></i>
                            <span>${session.device || 'Unknown Device'}</span>
                        </div>
                        <div class="session-info">
                            <i class="fas fa-globe"></i>
                            <span>${session.ip_address}</span>
                        </div>
                        <div class="session-info">
                            <i class="fas fa-map-marker-alt"></i>
                            <span>${session.location || 'Unknown Location'}</span>
                        </div>
                        <div class="session-info">
                            <i class="fas fa-clock"></i>
                            <span>Last active: ${Utils.formatDate(session.last_activity)}</span>
                        </div>
                    </div>
                    ${!session.is_current ? `
                        <div class="session-actions">
                            <button class="btn-danger btn-sm" onclick="SecurityManager.terminateSession('${session.id}')">
                                <i class="fas fa-sign-out-alt"></i> Terminate Session
                            </button>
                        </div>
                    ` : ''}
                </div>
            `).join('');
    } catch (error) {
      console.error('Error loading sessions:', error);
      container.innerHTML = '<p style="text-align: center; color: #ef4444;">Error loading sessions</p>';
    }
  },

  /**
   * Terminate session
   */
  async terminateSession(sessionId) {
    if (!confirm('Are you sure you want to terminate this session?')) return;

    try {
      await API.delete(`/security/sessions/${sessionId}/`);
      Utils.showToast('Session terminated successfully', 'success');
      this.loadActiveSessions();
    } catch (error) {
      console.error('Error terminating session:', error);
      Utils.showToast('Failed to terminate session', 'error');
    }
  },

  /**
   * Load security logs
   */
  async loadSecurityLogs() {
    const container = document.getElementById('logsContainer');
    if (!container) return;

    container.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i></div>';

    try {
      const logs = await API.get('/security/logs/');

      if (logs.length === 0) {
        container.innerHTML = '<p style="text-align: center; padding: 2rem;">No security logs</p>';
        return;
      }

      container.innerHTML = `
                <div class="logs-timeline">
                    ${logs.map(log => {
        const eventInfo = this.getEventInfo(log.event_type);
        return `
                            <div class="log-item">
                                <div class="log-marker ${eventInfo.class}">
                                    <i class="${eventInfo.icon}"></i>
                                </div>
                                <div class="log-content">
                                    <div class="log-header">
                                        <h4>${eventInfo.label}</h4>
                                        <span class="log-time">${Utils.formatDate(log.timestamp)}</span>
                                    </div>
                                    <p class="log-user">User: ${log.user?.username || 'System'}</p>
                                    <p class="log-details">${log.details || ''}</p>
                                    ${log.ip_address ? `<p class="log-ip">IP: <code>${log.ip_address}</code></p>` : ''}
                                </div>
                            </div>
                        `;
      }).join('')}
                </div>
            `;
    } catch (error) {
      console.error('Error loading logs:', error);
      container.innerHTML = '<p style="text-align: center; color: #ef4444;">Error loading logs</p>';
    }
  },

  /**
   * Get event info
   */
  getEventInfo(eventType) {
    const events = {
      login: { icon: 'fas fa-sign-in-alt', class: 'event-login', label: 'Login' },
      logout: { icon: 'fas fa-sign-out-alt', class: 'event-logout', label: 'Logout' },
      password_change: { icon: 'fas fa-key', class: 'event-password', label: 'Password Changed' },
      '2fa_enabled': { icon: 'fas fa-shield-alt', class: 'event-2fa', label: '2FA Enabled' },
      '2fa_disabled': { icon: 'fas fa-shield-alt', class: 'event-2fa', label: '2FA Disabled' },
      suspicious_activity: { icon: 'fas fa-exclamation-triangle', class: 'event-suspicious', label: 'Suspicious Activity' },
      account_locked: { icon: 'fas fa-lock', class: 'event-lock', label: 'Account Locked' },
      ip_blocked: { icon: 'fas fa-ban', class: 'event-block', label: 'IP Blocked' }
    };
    return events[eventType] || { icon: 'fas fa-info-circle', class: 'event-info', label: eventType };
  },

  /**
   * Load IP blacklist
   */
  async loadBlacklist() {
    const container = document.getElementById('blacklistContainer');
    if (!container) return;

    container.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i></div>';

    try {
      const blacklist = await API.get('/security/blacklist/');

      if (blacklist.length === 0) {
        container.innerHTML = '<p style="text-align: center; padding: 2rem;">No blocked IPs</p>';
        return;
      }

      container.innerHTML = `
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>IP Address</th>
                            <th>Reason</th>
                            <th>Blocked Date</th>
                            <th>Expires</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${blacklist.map(item => `
                            <tr>
                                <td><code>${item.ip_address}</code></td>
                                <td>${item.reason || 'No reason provided'}</td>
                                <td>${Utils.formatDate(item.created_at)}</td>
                                <td>${item.expires_at ? Utils.formatDate(item.expires_at) : 'Never'}</td>
                                <td>
                                    <button class="btn-icon btn-success" onclick="SecurityManager.unblockIP('${item.ip_address}')" title="Unblock">
                                        <i class="fas fa-check"></i>
                                    </button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
    } catch (error) {
      console.error('Error loading blacklist:', error);
      container.innerHTML = '<p style="text-align: center; color: #ef4444;">Error loading blacklist</p>';
    }
  },

  /**
   * Block IP
   */
  async blockIP(ipAddress) {
    const reason = prompt('Reason for blocking this IP:');
    if (!reason) return;

    try {
      await API.post('/security/blacklist/', {
        ip_address: ipAddress,
        reason: reason
      });
      Utils.showToast('IP blocked successfully', 'success');
      this.loadBlacklist();
      this.loadOverview();
    } catch (error) {
      console.error('Error blocking IP:', error);
      Utils.showToast('Failed to block IP', 'error');
    }
  },

  /**
   * Unblock IP
   */
  async unblockIP(ipAddress) {
    if (!confirm(`Unblock IP ${ipAddress}?`)) return;

    try {
      await API.delete(`/security/blacklist/${ipAddress}/`);
      Utils.showToast('IP unblocked successfully', 'success');
      this.loadBlacklist();
      this.loadOverview();
    } catch (error) {
      console.error('Error unblocking IP:', error);
      Utils.showToast('Failed to unblock IP', 'error');
    }
  },

  /**
   * Lock account
   */
  async lockAccount(userId) {
    if (!confirm('Lock this user account?')) return;

    try {
      await API.post(`/users/${userId}/lock/`, {});
      Utils.showToast('Account locked successfully', 'success');
    } catch (error) {
      console.error('Error locking account:', error);
      Utils.showToast('Failed to lock account', 'error');
    }
  },

  /**
   * Handle add IP
   */
  async handleAddIp() {
    const ipAddress = document.getElementById('addIpAddress').value;
    const reason = document.getElementById('addIpReason').value;
    const expiresAt = document.getElementById('addIpExpires').value;

    try {
      await API.post('/security/blacklist/', {
        ip_address: ipAddress,
        reason: reason,
        expires_at: expiresAt || null
      });
      Utils.showToast('IP added to blacklist', 'success');
      Modals.close('addIpModal');
      document.getElementById('addIpForm').reset();
      this.loadBlacklist();
      this.loadOverview();
    } catch (error) {
      console.error('Error adding IP:', error);
      Utils.showToast('Failed to add IP', 'error');
    }
  },

  /**
   * Export logs
   */
  async exportLogs() {
    try {
      const logs = await API.get('/security/logs/export/');
      const blob = new Blob([JSON.stringify(logs, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `security-logs-${new Date().toISOString()}.json`;
      link.click();
      Utils.showToast('Logs exported successfully', 'success');
    } catch (error) {
      console.error('Error exporting logs:', error);
      Utils.showToast('Failed to export logs', 'error');
    }
  }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
  module.exports = SecurityManager;
}
