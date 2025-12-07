/**
 * Users Management
 * Enhanced user management with CRUD, filtering, sorting, bulk actions
 */

const UsersManager = {
  currentPage: 1,
  perPage: 20,
  sortBy: 'date_joined',
  sortOrder: 'desc',
  filters: {
    search: '',
    status: 'all',
    verified: 'all',
    provider: 'all'
  },
  selectedUsers: new Set(),

  /**
   * Initialize users management
   */
  init() {
    this.setupEventListeners();
    this.loadUsers();
  },

  /**
   * Setup event listeners
   */
  setupEventListeners() {
    // Search
    const searchInput = document.getElementById('userSearch');
    if (searchInput) {
      searchInput.addEventListener('input', Utils.debounce((e) => {
        this.filters.search = e.target.value;
        this.currentPage = 1;
        this.loadUsers();
      }, 300));
    }

    // Filters
    ['userStatusFilter', 'userVerifiedFilter', 'userProviderFilter'].forEach(id => {
      const filter = document.getElementById(id);
      if (filter) {
        filter.addEventListener('change', (e) => {
          const filterName = id.replace('user', '').replace('Filter', '').toLowerCase();
          this.filters[filterName] = e.target.value;
          this.currentPage = 1;
          this.loadUsers();
        });
      }
    });

    // Sortable columns
    document.querySelectorAll('th.sortable').forEach(th => {
      th.addEventListener('click', () => {
        const sortField = th.dataset.sort;
        if (this.sortBy === sortField) {
          this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc';
        } else {
          this.sortBy = sortField;
          this.sortOrder = 'asc';
        }
        this.updateSortUI();
        this.loadUsers();
      });
    });

    // Select all checkbox
    const selectAll = document.getElementById('selectAllUsers');
    if (selectAll) {
      selectAll.addEventListener('change', (e) => {
        this.toggleSelectAll(e.target.checked);
      });
    }

    // Add user button
    const addUserBtn = document.getElementById('addUserBtn');
    if (addUserBtn) {
      addUserBtn.addEventListener('click', () => {
        Modals.open('addUserModal');
      });
    }

    // Add user form
    const addUserForm = document.getElementById('addUserForm');
    if (addUserForm) {
      addUserForm.addEventListener('submit', (e) => {
        e.preventDefault();
        this.handleAddUser();
      });
    }

    // Edit user form
    const editUserForm = document.getElementById('editUserForm');
    if (editUserForm) {
      editUserForm.addEventListener('submit', (e) => {
        e.preventDefault();
        this.handleEditUser();
      });
    }

    // Bulk actions
    const bulkDeleteBtn = document.getElementById('bulkDeleteBtn');
    if (bulkDeleteBtn) {
      bulkDeleteBtn.addEventListener('click', () => this.handleBulkDelete());
    }

    const bulkExportBtn = document.getElementById('bulkExportBtn');
    if (bulkExportBtn) {
      bulkExportBtn.addEventListener('click', () => this.handleBulkExport());
    }

    const clearSelectionBtn = document.getElementById('clearSelectionBtn');
    if (clearSelectionBtn) {
      clearSelectionBtn.addEventListener('click', () => this.clearSelection());
    }

    // Export button
    const exportBtn = document.getElementById('exportUsersBtn');
    if (exportBtn) {
      exportBtn.addEventListener('click', () => this.exportUsers());
    }
  },

  /**
   * Load users
   */
  async loadUsers() {
    const tableBody = document.getElementById('usersTableBody');
    const mobileCards = document.getElementById('usersMobileCards');

    if (tableBody) {
      tableBody.innerHTML = '<tr><td colspan="7" class="loading-cell"><i class="fas fa-spinner fa-spin"></i> Loading users...</td></tr>';
    }

    try {
      const params = {
        page: this.currentPage,
        page_size: this.perPage,
        ordering: this.sortOrder === 'desc' ? `-${this.sortBy}` : this.sortBy
      };

      if (this.filters.search) params.search = this.filters.search;
      if (this.filters.status !== 'all') params.is_active = this.filters.status === 'active';
      if (this.filters.verified !== 'all') params.email_verified = this.filters.verified === 'verified';
      if (this.filters.provider !== 'all') params.auth_provider = this.filters.provider;

      const response = await API.getUsers(params);
      const users = response.results || response;

      this.renderUsers(users);
      this.renderPagination(response);
    } catch (error) {
      console.error('Error loading users:', error);
      if (tableBody) {
        tableBody.innerHTML = '<tr><td colspan="7" class="loading-cell">Error loading users</td></tr>';
      }
      Utils.showToast('Failed to load users', 'error');
    }
  },

  /**
   * Render users table
   */
  renderUsers(users) {
    const tableBody = document.getElementById('usersTableBody');
    const mobileCards = document.getElementById('usersMobileCards');

    if (users.length === 0) {
      if (tableBody) {
        tableBody.innerHTML = '<tr><td colspan="7" class="loading-cell">No users found</td></tr>';
      }
      if (mobileCards) {
        mobileCards.innerHTML = '<p style="text-align: center; padding: 2rem;">No users found</p>';
      }
      return;
    }

    // Table view
    if (tableBody) {
      tableBody.innerHTML = users.map(user => `
                <tr>
                    <td>
                        <input type="checkbox" class="user-checkbox" data-user-id="${user.id}" 
                               ${this.selectedUsers.has(user.id) ? 'checked' : ''}>
                    </td>
                    <td>
                        <div style="display: flex; align-items: center; gap: 0.5rem;">
                            <img src="${user.profile_picture || `https://ui-avatars.com/api/?name=${encodeURIComponent(user.username)}`}" 
                                 alt="${user.username}" 
                                 style="width: 32px; height: 32px; border-radius: 50%;">
                            <span>${user.username}</span>
                        </div>
                    </td>
                    <td>${user.email}</td>
                    <td>
                        ${user.email_verified ?
          '<span class="badge badge-success"><i class="fas fa-check-circle"></i> Verified</span>' :
          '<span class="badge badge-warning"><i class="fas fa-exclamation-circle"></i> Unverified</span>'}
                    </td>
                    <td>
                        <span class="badge badge-info">
                            ${this.getProviderIcon(user.auth_provider)} ${user.auth_provider || 'Email'}
                        </span>
                    </td>
                    <td>${Utils.formatDate(user.date_joined || user.created_at)}</td>
                    <td>
                        <div style="display: flex; gap: 0.25rem;">
                            <button class="btn-icon" onclick="UsersManager.viewUser(${user.id})" title="View">
                                <i class="fas fa-eye"></i>
                            </button>
                            <button class="btn-icon" onclick="UsersManager.editUser(${user.id})" title="Edit">
                                <i class="fas fa-edit"></i>
                            </button>
                            ${user.is_active ?
          `<button class="btn-icon" onclick="UsersManager.banUser(${user.id})" title="Ban">
                                    <i class="fas fa-ban"></i>
                                </button>` :
          `<button class="btn-icon" onclick="UsersManager.unbanUser(${user.id})" title="Unban">
                                    <i class="fas fa-check-circle"></i>
                                </button>`}
                            ${!user.email_verified ?
          `<button class="btn-icon" onclick="UsersManager.verifyEmail(${user.id})" title="Verify Email">
                                    <i class="fas fa-envelope-circle-check"></i>
                                </button>` : ''}
                            <button class="btn-icon btn-danger" onclick="UsersManager.deleteUser(${user.id})" title="Delete">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `).join('');

      // Add checkbox listeners
      document.querySelectorAll('.user-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', (e) => {
          const userId = parseInt(e.target.dataset.userId);
          if (e.target.checked) {
            this.selectedUsers.add(userId);
          } else {
            this.selectedUsers.delete(userId);
          }
          this.updateBulkActions();
        });
      });
    }

    // Mobile card view
    if (mobileCards) {
      mobileCards.innerHTML = users.map(user => `
                <div class="user-card">
                    <div class="user-card-header">
                        <img src="${user.profile_picture || `https://ui-avatars.com/api/?name=${encodeURIComponent(user.username)}`}" 
                             alt="${user.username}" 
                             class="user-card-avatar">
                        <div class="user-card-info">
                            <h4>${user.username}</h4>
                            <p>${user.email}</p>
                        </div>
                    </div>
                    <div class="user-card-details">
                        <div class="user-card-detail">
                            <strong>Verified</strong>
                            ${user.email_verified ? '<span class="badge badge-success">Yes</span>' : '<span class="badge badge-warning">No</span>'}
                        </div>
                        <div class="user-card-detail">
                            <strong>Provider</strong>
                            ${user.auth_provider || 'Email'}
                        </div>
                        <div class="user-card-detail">
                            <strong>Joined</strong>
                            ${Utils.formatDate(user.date_joined || user.created_at)}
                        </div>
                        <div class="user-card-detail">
                            <strong>Status</strong>
                            ${user.is_active ? '<span class="badge badge-success">Active</span>' : '<span class="badge badge-danger">Banned</span>'}
                        </div>
                    </div>
                    <div class="user-card-actions">
                        <button class="btn-secondary btn-sm" onclick="UsersManager.viewUser(${user.id})">
                            <i class="fas fa-eye"></i> View
                        </button>
                        <button class="btn-secondary btn-sm" onclick="UsersManager.editUser(${user.id})">
                            <i class="fas fa-edit"></i> Edit
                        </button>
                        <button class="btn-danger btn-sm" onclick="UsersManager.deleteUser(${user.id})">
                            <i class="fas fa-trash"></i> Delete
                        </button>
                    </div>
                </div>
            `).join('');
    }
  },

  /**
   * Get provider icon
   */
  getProviderIcon(provider) {
    const icons = {
      google: '<i class="fab fa-google"></i>',
      microsoft: '<i class="fab fa-microsoft"></i>',
      email: '<i class="fas fa-envelope"></i>'
    };
    return icons[provider] || icons.email;
  },

  /**
   * Update sort UI
   */
  updateSortUI() {
    document.querySelectorAll('th.sortable').forEach(th => {
      th.classList.remove('sorted-asc', 'sorted-desc');
      if (th.dataset.sort === this.sortBy) {
        th.classList.add(`sorted-${this.sortOrder}`);
      }
    });
  },

  /**
   * Toggle select all
   */
  toggleSelectAll(checked) {
    document.querySelectorAll('.user-checkbox').forEach(checkbox => {
      checkbox.checked = checked;
      const userId = parseInt(checkbox.dataset.userId);
      if (checked) {
        this.selectedUsers.add(userId);
      } else {
        this.selectedUsers.delete(userId);
      }
    });
    this.updateBulkActions();
  },

  /**
   * Update bulk actions visibility
   */
  updateBulkActions() {
    const bulkActions = document.getElementById('bulkActions');
    const selectedCount = document.getElementById('selectedCount');

    if (this.selectedUsers.size > 0) {
      if (bulkActions) bulkActions.style.display = 'flex';
      if (selectedCount) selectedCount.textContent = this.selectedUsers.size;
    } else {
      if (bulkActions) bulkActions.style.display = 'none';
    }
  },

  /**
   * Clear selection
   */
  clearSelection() {
    this.selectedUsers.clear();
    document.querySelectorAll('.user-checkbox').forEach(cb => cb.checked = false);
    document.getElementById('selectAllUsers').checked = false;
    this.updateBulkActions();
  },

  /**
   * View user details
   */
  async viewUser(id) {
    Modals.open('userDetailsModal');
    const body = document.getElementById('userDetailsBody');
    body.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i></div>';

    try {
      const user = await API.getUser(id);
      body.innerHTML = `
                <div class="user-details-grid">
                    <div class="user-details-sidebar">
                        <img src="${user.profile_picture || `https://ui-avatars.com/api/?name=${encodeURIComponent(user.username)}`}" 
                             alt="${user.username}" 
                             class="user-details-avatar">
                        <h3 class="user-details-name">${user.username}</h3>
                        <p class="user-details-email">${user.email}</p>
                        ${user.email_verified ?
          '<span class="badge badge-success"><i class="fas fa-check-circle"></i> Verified</span>' :
          '<span class="badge badge-warning"><i class="fas fa-exclamation-circle"></i> Unverified</span>'}
                    </div>
                    <div class="user-details-content">
                        <div class="user-details-stats">
                            <div class="user-stat">
                                <div class="user-stat-value">${user.posts_count || 0}</div>
                                <div class="user-stat-label">Posts</div>
                            </div>
                            <div class="user-stat">
                                <div class="user-stat-value">${user.followers_count || 0}</div>
                                <div class="user-stat-label">Followers</div>
                            </div>
                            <div class="user-stat">
                                <div class="user-stat-value">${user.following_count || 0}</div>
                                <div class="user-stat-label">Following</div>
                            </div>
                        </div>

                        <div class="user-details-section">
                            <h4>Account Information</h4>
                            <div class="user-details-row">
                                <div class="user-details-label">Full Name</div>
                                <div class="user-details-value">${user.first_name || ''} ${user.last_name || ''}</div>
                            </div>
                            <div class="user-details-row">
                                <div class="user-details-label">Bio</div>
                                <div class="user-details-value">${user.bio || 'No bio'}</div>
                            </div>
                            <div class="user-details-row">
                                <div class="user-details-label">Auth Provider</div>
                                <div class="user-details-value">${user.auth_provider || 'Email'}</div>
                            </div>
                            <div class="user-details-row">
                                <div class="user-details-label">Joined</div>
                                <div class="user-details-value">${Utils.formatDate(user.date_joined || user.created_at)}</div>
                            </div>
                            <div class="user-details-row">
                                <div class="user-details-label">Status</div>
                                <div class="user-details-value">
                                    ${user.is_active ? '<span class="badge badge-success">Active</span>' : '<span class="badge badge-danger">Banned</span>'}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
    } catch (error) {
      console.error('Error loading user:', error);
      body.innerHTML = '<p style="text-align: center; color: #ef4444;">Error loading user details</p>';
    }
  },

  /**
   * Edit user
   */
  async editUser(id) {
    try {
      const user = await API.getUser(id);

      document.getElementById('editUserId').value = user.id;
      document.getElementById('editUsername').value = user.username;
      document.getElementById('editEmail').value = user.email;
      document.getElementById('editFirstName').value = user.first_name || '';
      document.getElementById('editLastName').value = user.last_name || '';
      document.getElementById('editBio').value = user.bio || '';
      document.getElementById('editIsActive').checked = user.is_active;

      Modals.open('editUserModal');
    } catch (error) {
      console.error('Error loading user:', error);
      Utils.showToast('Failed to load user', 'error');
    }
  },

  /**
   * Handle add user
   */
  async handleAddUser() {
    const formData = {
      username: document.getElementById('addUsername').value,
      email: document.getElementById('addEmail').value,
      password: document.getElementById('addPassword').value,
      first_name: document.getElementById('addFirstName').value,
      last_name: document.getElementById('addLastName').value,
      bio: document.getElementById('addBio').value
    };

    try {
      await API.createUser(formData);
      Utils.showToast('User created successfully', 'success');
      Modals.close('addUserModal');
      document.getElementById('addUserForm').reset();
      this.loadUsers();
    } catch (error) {
      console.error('Error creating user:', error);
      Utils.showToast('Failed to create user', 'error');
    }
  },

  /**
   * Handle edit user
   */
  async handleEditUser() {
    const id = document.getElementById('editUserId').value;
    const formData = {
      username: document.getElementById('editUsername').value,
      email: document.getElementById('editEmail').value,
      first_name: document.getElementById('editFirstName').value,
      last_name: document.getElementById('editLastName').value,
      bio: document.getElementById('editBio').value,
      is_active: document.getElementById('editIsActive').checked
    };

    try {
      await API.updateUser(id, formData);
      Utils.showToast('User updated successfully', 'success');
      Modals.close('editUserModal');
      this.loadUsers();
    } catch (error) {
      console.error('Error updating user:', error);
      Utils.showToast('Failed to update user', 'error');
    }
  },

  /**
   * Delete user
   */
  async deleteUser(id) {
    if (!confirm('Are you sure you want to delete this user?')) return;

    try {
      await API.deleteUser(id);
      Utils.showToast('User deleted successfully', 'success');
      this.loadUsers();
    } catch (error) {
      console.error('Error deleting user:', error);
      Utils.showToast('Failed to delete user', 'error');
    }
  },

  /**
   * Ban user
   */
  async banUser(id) {
    if (!confirm('Are you sure you want to ban this user?')) return;

    try {
      await API.post(`/users/${id}/ban/`, {});
      Utils.showToast('User banned successfully', 'success');
      this.loadUsers();
    } catch (error) {
      console.error('Error banning user:', error);
      Utils.showToast('Failed to ban user', 'error');
    }
  },

  /**
   * Unban user
   */
  async unbanUser(id) {
    try {
      await API.updateUser(id, { is_active: true });
      Utils.showToast('User unbanned successfully', 'success');
      this.loadUsers();
    } catch (error) {
      console.error('Error unbanning user:', error);
      Utils.showToast('Failed to unban user', 'error');
    }
  },

  /**
   * Verify email
   */
  async verifyEmail(id) {
    try {
      await API.post(`/users/${id}/verify-email/`, {});
      Utils.showToast('Email verified successfully', 'success');
      this.loadUsers();
    } catch (error) {
      console.error('Error verifying email:', error);
      Utils.showToast('Failed to verify email', 'error');
    }
  },

  /**
   * Handle bulk delete
   */
  async handleBulkDelete() {
    if (!confirm(`Are you sure you want to delete ${this.selectedUsers.size} users?`)) return;

    try {
      await Promise.all(
        Array.from(this.selectedUsers).map(id => API.deleteUser(id))
      );
      Utils.showToast(`${this.selectedUsers.size} users deleted successfully`, 'success');
      this.clearSelection();
      this.loadUsers();
    } catch (error) {
      console.error('Error deleting users:', error);
      Utils.showToast('Failed to delete some users', 'error');
    }
  },

  /**
   * Handle bulk export
   */
  handleBulkExport() {
    Utils.showToast('Export feature coming soon', 'info');
  },

  /**
   * Export users
   */
  exportUsers() {
    Utils.showToast('Export feature coming soon', 'info');
  },

  /**
   * Render pagination
   */
  renderPagination(response) {
    const pagination = document.getElementById('usersPagination');
    if (!pagination || !response.count) return;

    const totalPages = Math.ceil(response.count / this.perPage);
    if (totalPages <= 1) {
      pagination.innerHTML = '';
      return;
    }

    let html = '<div class="pagination">';

    // Previous button
    html += `<button class="pagination-btn" ${this.currentPage === 1 ? 'disabled' : ''} 
                 onclick="UsersManager.goToPage(${this.currentPage - 1})">
                 <i class="fas fa-chevron-left"></i>
                 </button>`;

    // Page numbers
    for (let i = 1; i <= Math.min(totalPages, 5); i++) {
      html += `<button class="pagination-btn ${i === this.currentPage ? 'active' : ''}" 
                     onclick="UsersManager.goToPage(${i})">${i}</button>`;
    }

    // Next button
    html += `<button class="pagination-btn" ${this.currentPage === totalPages ? 'disabled' : ''} 
                 onclick="UsersManager.goToPage(${this.currentPage + 1})">
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
    this.loadUsers();
  }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
  module.exports = UsersManager;
}
