/**
 * ChattingUs Admin Dashboard - Main Dashboard Logic
 * Handles dashboard functionality, data loading, and user interactions
 */

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  Dashboard.init();
});

const Dashboard = {
  // Current page state
  currentPage: 'dashboard',
  charts: {},

  /**
   * Initialize dashboard
   */
  init() {
    // Require authentication
    Utils.requireAuth();

    // Initialize theme
    Utils.initTheme();

    // Load user info
    this.loadUserInfo();

    // Setup event listeners
    this.setupEventListeners();

    // Load initial data
    this.loadDashboardData();
  },

  /**
   * Setup event listeners
   */
  setupEventListeners() {
    // Navigation
    document.querySelectorAll('.nav-item[data-page]').forEach(item => {
      item.addEventListener('click', (e) => {
        e.preventDefault();
        const page = item.dataset.page;
        this.navigateToPage(page);
      });
    });

    // Mobile menu toggle
    const mobileMenuToggle = document.getElementById('mobileMenuToggle');
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');

    if (mobileMenuToggle) {
      mobileMenuToggle.addEventListener('click', () => {
        sidebar.classList.toggle('active');
        sidebarOverlay.classList.toggle('active');
      });
    }

    if (sidebarOverlay) {
      sidebarOverlay.addEventListener('click', () => {
        sidebar.classList.remove('active');
        sidebarOverlay.classList.remove('active');
      });
    }

    // Theme toggle
    const themeToggleBtn = document.getElementById('themeToggleBtn');
    if (themeToggleBtn) {
      themeToggleBtn.addEventListener('click', () => {
        Utils.toggleTheme();
      });
    }

    // Logout
    const logoutBtn = document.getElementById('logoutBtn');
    const logoutLink = document.getElementById('logoutLink');

    [logoutBtn, logoutLink].forEach(btn => {
      if (btn) {
        btn.addEventListener('click', (e) => {
          e.preventDefault();
          this.handleLogout();
        });
      }
    });

    // Global search
    const globalSearch = document.getElementById('globalSearch');
    if (globalSearch) {
      globalSearch.addEventListener('input', Utils.debounce((e) => {
        this.handleGlobalSearch(e.target.value);
      }, 300));
    }

    // User search
    const userSearch = document.getElementById('userSearch');
    if (userSearch) {
      userSearch.addEventListener('input', Utils.debounce((e) => {
        this.loadUsers({ search: e.target.value });
      }, 300));
    }

    // Post search
    const postSearch = document.getElementById('postSearch');
    if (postSearch) {
      postSearch.addEventListener('input', Utils.debounce((e) => {
        this.loadPosts({ search: e.target.value });
      }, 300));
    }
  },

  /**
   * Load user info
   */
  loadUserInfo() {
    const user = Auth.getCurrentUser();
    if (user) {
      const userName = document.getElementById('userName');
      if (userName) {
        userName.textContent = user.username || user.email || 'Admin';
      }

      // Update avatar
      const userAvatar = document.querySelector('.user-avatar img');
      if (userAvatar && user.profile_picture) {
        userAvatar.src = user.profile_picture;
      }
    }
  },

  /**
   * Navigate to page
   * @param {string} page - Page name
   */
  navigateToPage(page) {
    // Update active nav item
    document.querySelectorAll('.nav-item').forEach(item => {
      item.classList.remove('active');
    });
    document.querySelector(`.nav-item[data-page="${page}"]`)?.classList.add('active');

    // Update page title
    const pageTitle = document.getElementById('pageTitle');
    if (pageTitle) {
      pageTitle.textContent = page.charAt(0).toUpperCase() + page.slice(1);
    }

    // Show corresponding section
    document.querySelectorAll('.content-section').forEach(section => {
      section.classList.remove('active');
    });
    document.getElementById(`${page}Section`)?.classList.add('active');

    // Load page data
    this.currentPage = page;
    this.loadPageData(page);

    // Close mobile menu
    document.getElementById('sidebar')?.classList.remove('active');
    document.getElementById('sidebarOverlay')?.classList.remove('active');
  },

  /**
   * Load page data
   * @param {string} page - Page name
   */
  async loadPageData(page) {
    switch (page) {
      case 'dashboard':
        await this.loadDashboardData();
        break;
      case 'users':
        // Use enhanced UsersManager
        if (typeof UsersManager !== 'undefined') {
          UsersManager.init();
        } else {
          await this.loadUsers();
        }
        break;
      case 'posts':
        // Use enhanced PostsManager
        if (typeof PostsManager !== 'undefined') {
          PostsManager.init();
        } else {
          await this.loadPosts();
        }
        break;
      case 'comments':
        // Use enhanced ModerationManager for reports
        if (typeof ModerationManager !== 'undefined') {
          ModerationManager.init();
        } else {
          await this.loadComments();
        }
        break;
      case 'stories':
        // Use enhanced StoriesManager
        if (typeof StoriesManager !== 'undefined') {
          StoriesManager.init();
        } else {
          await this.loadStories();
        }
        break;
      case 'reels':
        // Use enhanced ReelsManager
        if (typeof ReelsManager !== 'undefined') {
          ReelsManager.init();
        }
        break;
      case 'live':
        // Use enhanced LiveStreamsManager
        if (typeof LiveStreamsManager !== 'undefined') {
          LiveStreamsManager.init();
        } else {
          await this.loadLiveStreams();
        }
        break;
      case 'analytics':
        // Use enhanced SecurityManager for security page
        if (typeof SecurityManager !== 'undefined') {
          SecurityManager.init();
        } else {
          await this.loadAnalytics();
        }
        break;
      case 'notifications':
        // Use enhanced NotificationsManager
        if (typeof NotificationsManager !== 'undefined') {
          NotificationsManager.init();
        } else {
          await this.loadNotifications();
        }
        break;
    }
  },

  /**
   * Load dashboard data
   */
  async loadDashboardData() {
    try {
      // Load stats
      const stats = await API.getDashboardStats();
      this.updateStats(stats);

      // Load charts
      this.initializeCharts();

      // Load recent activity
      await this.loadRecentActivity();
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      Utils.showToast('Failed to load dashboard data', 'error');
    }
  },

  /**
   * Update stats
   * @param {object} stats - Statistics data
   */
  updateStats(stats) {
    if (stats.total_users !== undefined) {
      document.getElementById('totalUsers').textContent = Utils.formatNumber(stats.total_users);
    }
    if (stats.total_posts !== undefined) {
      document.getElementById('totalPosts').textContent = Utils.formatNumber(stats.total_posts);
    }
    if (stats.total_comments !== undefined) {
      document.getElementById('totalComments').textContent = Utils.formatNumber(stats.total_comments);
    }
    if (stats.active_live_streams !== undefined) {
      document.getElementById('activeLiveStreams').textContent = Utils.formatNumber(stats.active_live_streams);
    }
  },

  /**
   * Initialize charts
   */
  initializeCharts() {
    // User Growth Chart
    const userGrowthCtx = document.getElementById('userGrowthChart');
    if (userGrowthCtx && !this.charts.userGrowth) {
      this.charts.userGrowth = new Chart(userGrowthCtx, {
        type: 'line',
        data: {
          labels: ['Day 1', 'Day 7', 'Day 14', 'Day 21', 'Day 30'],
          datasets: [{
            label: 'New Users',
            data: [12, 19, 25, 32, 45],
            borderColor: '#8b5cf6',
            backgroundColor: 'rgba(139, 92, 246, 0.1)',
            tension: 0.4,
            fill: true
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: false
            }
          },
          scales: {
            y: {
              beginAtZero: true
            }
          }
        }
      });
    }

    // Content Activity Chart
    const contentActivityCtx = document.getElementById('contentActivityChart');
    if (contentActivityCtx && !this.charts.contentActivity) {
      this.charts.contentActivity = new Chart(contentActivityCtx, {
        type: 'bar',
        data: {
          labels: ['Posts', 'Comments', 'Stories', 'Live Streams'],
          datasets: [{
            label: 'Activity',
            data: [65, 120, 45, 8],
            backgroundColor: [
              'rgba(139, 92, 246, 0.8)',
              'rgba(236, 72, 153, 0.8)',
              'rgba(6, 182, 212, 0.8)',
              'rgba(250, 112, 154, 0.8)'
            ]
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: false
            }
          },
          scales: {
            y: {
              beginAtZero: true
            }
          }
        }
      });
    }
  },

  /**
   * Load recent activity
   */
  async loadRecentActivity() {
    const activityList = document.getElementById('activityList');
    if (!activityList) return;

    activityList.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i></div>';

    // Simulated activity data - replace with actual API call
    const activities = [
      { type: 'user', message: 'New user registered', time: '2 minutes ago' },
      { type: 'post', message: 'New post created', time: '5 minutes ago' },
      { type: 'comment', message: 'New comment added', time: '10 minutes ago' }
    ];

    activityList.innerHTML = activities.map(activity => `
            <div class="activity-item">
                <i class="fas fa-${this.getActivityIcon(activity.type)}"></i>
                <div>
                    <p>${activity.message}</p>
                    <span>${activity.time}</span>
                </div>
            </div>
        `).join('');
  },

  /**
   * Get activity icon
   * @param {string} type - Activity type
   * @returns {string}
   */
  getActivityIcon(type) {
    const icons = {
      user: 'user-plus',
      post: 'image',
      comment: 'comment',
      story: 'bolt',
      live: 'video'
    };
    return icons[type] || 'circle';
  },

  /**
   * Load users
   * @param {object} params - Query parameters
   */
  async loadUsers(params = {}) {
    const tableBody = document.getElementById('usersTableBody');
    if (!tableBody) return;

    tableBody.innerHTML = '<tr><td colspan="6" class="loading-cell"><i class="fas fa-spinner fa-spin"></i> Loading users...</td></tr>';

    try {
      const response = await API.getUsers(params);
      const users = response.results || response;

      if (users.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="6" class="loading-cell">No users found</td></tr>';
        return;
      }

      tableBody.innerHTML = users.map(user => `
                <tr>
                    <td>
                        <div style="display: flex; align-items: center; gap: 0.5rem;">
                            <img src="${user.profile_picture || `https://ui-avatars.com/api/?name=${encodeURIComponent(user.username || user.email)}`}" 
                                 alt="${user.username}" 
                                 style="width: 32px; height: 32px; border-radius: 50%;">
                            <span>${user.username || user.email}</span>
                        </div>
                    </td>
                    <td>${user.email}</td>
                    <td>${Utils.formatDate(user.date_joined || user.created_at)}</td>
                    <td>${user.posts_count || 0}</td>
                    <td>
                        <span class="badge ${user.is_active ? 'badge-success' : 'badge-danger'}">
                            ${user.is_active ? 'Active' : 'Inactive'}
                        </span>
                    </td>
                    <td>
                        <button class="btn-icon" onclick="Dashboard.viewUser(${user.id})" title="View">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn-icon" onclick="Dashboard.editUser(${user.id})" title="Edit">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn-icon btn-danger" onclick="Dashboard.deleteUser(${user.id})" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `).join('');
    } catch (error) {
      console.error('Error loading users:', error);
      tableBody.innerHTML = '<tr><td colspan="6" class="loading-cell">Error loading users</td></tr>';
      Utils.showToast('Failed to load users', 'error');
    }
  },

  /**
   * Load posts
   * @param {object} params - Query parameters
   */
  async loadPosts(params = {}) {
    const tableBody = document.getElementById('postsTableBody');
    if (!tableBody) return;

    tableBody.innerHTML = '<tr><td colspan="6" class="loading-cell"><i class="fas fa-spinner fa-spin"></i> Loading posts...</td></tr>';

    try {
      const response = await API.getPosts(params);
      const posts = response.results || response;

      if (posts.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="6" class="loading-cell">No posts found</td></tr>';
        return;
      }

      tableBody.innerHTML = posts.map(post => `
                <tr>
                    <td>
                        <div style="display: flex; align-items: center; gap: 0.5rem;">
                            ${post.image ? `<img src="${post.image}" alt="Post" style="width: 50px; height: 50px; object-fit: cover; border-radius: 8px;">` : ''}
                            <span>${Utils.truncateText(post.caption || 'No caption', 50)}</span>
                        </div>
                    </td>
                    <td>${post.user?.username || post.user?.email || 'Unknown'}</td>
                    <td>${Utils.formatDate(post.created_at)}</td>
                    <td>${post.likes_count || 0}</td>
                    <td>${post.comments_count || 0}</td>
                    <td>
                        <button class="btn-icon" onclick="Dashboard.viewPost(${post.id})" title="View">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn-icon btn-danger" onclick="Dashboard.deletePost(${post.id})" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                </tr>
            `).join('');
    } catch (error) {
      console.error('Error loading posts:', error);
      tableBody.innerHTML = '<tr><td colspan="6" class="loading-cell">Error loading posts</td></tr>';
      Utils.showToast('Failed to load posts', 'error');
    }
  },

  /**
   * Delete user
   * @param {number} id - User ID
   */
  async deleteUser(id) {
    if (!confirm('Are you sure you want to delete this user?')) return;

    try {
      await API.deleteUser(id);
      Utils.showToast('User deleted successfully', 'success');
      await this.loadUsers();
    } catch (error) {
      console.error('Error deleting user:', error);
      Utils.showToast('Failed to delete user', 'error');
    }
  },

  /**
   * Delete post
   * @param {number} id - Post ID
   */
  async deletePost(id) {
    if (!confirm('Are you sure you want to delete this post?')) return;

    try {
      await API.deletePost(id);
      Utils.showToast('Post deleted successfully', 'success');
      await this.loadPosts();
    } catch (error) {
      console.error('Error deleting post:', error);
      Utils.showToast('Failed to delete post', 'error');
    }
  },

  /**
   * Handle logout
   */
  async handleLogout() {
    if (!confirm('Are you sure you want to logout?')) return;

    try {
      await Auth.logout();
    } catch (error) {
      console.error('Logout error:', error);
      // Still logout locally even if API call fails
      Auth.clearAuthData();
      window.location.href = 'index.html';
    }
  },

  /**
   * Handle global search
   * @param {string} query - Search query
   */
  handleGlobalSearch(query) {
    console.log('Global search:', query);
    // Implement global search logic
  },

  // Placeholder methods for CRUD operations
  viewUser(id) { console.log('View user:', id); },
  editUser(id) { console.log('Edit user:', id); },
  // View post details
  async viewPost(id) {
    try {
      const post = await API.getPost(id);

      // Format comments HTML
      let commentsHTML = '';
      if (post.comments && post.comments.length > 0) {
        commentsHTML = `
          <div class="post-comments">
            <h3>Comments (${post.comments.length})</h3>
            <div class="comments-list">
              ${post.comments.map(comment => `
                <div class="comment-item">
                  <div class="comment-user"><strong>${comment.user.username}</strong></div>
                  <div class="comment-text">${comment.text}</div>
                  <div class="comment-date">${new Date(comment.created_at).toLocaleString()}</div>
                </div>
              `).join('')}
            </div>
          </div>
        `;
      } else {
        commentsHTML = '<div class="post-comments"><p>No comments yet</p></div>';
      }

      // Create modal HTML
      const modalHTML = `
        <div class="modal-overlay" id="postModal">
          <div class="modal-content">
            <div class="modal-header">
              <h2>Post Details</h2>
              <button class="modal-close" onclick="Dashboard.closeModal('postModal')">&times;</button>
            </div>
            <div class="modal-body">
              <div class="post-detail">
                <div class="post-user">
                  <strong>User:</strong> ${post.user.username} (${post.user.email})
                </div>
                <div class="post-caption">
                  <strong>Caption:</strong> ${post.caption || 'No caption'}
                </div>
                <div class="post-stats">
                  <span><i class="fas fa-heart"></i> ${post.likes_count} likes</span>
                  <span><i class="fas fa-comment"></i> ${post.comments_count} comments</span>
                </div>
                <div class="post-date">
                  <strong>Created:</strong> ${new Date(post.created_at).toLocaleString()}
                </div>
                ${commentsHTML}
              </div>
            </div>
          </div>
        </div>
      `;

      // Add modal to page
      document.body.insertAdjacentHTML('beforeend', modalHTML);
    } catch (error) {
      console.error('Error loading post:', error);
      Utils.showToast('Failed to load post details', 'error');
    }
  },

  // Close modal
  closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.remove();
    }
  },

  loadComments() { console.log('Load comments'); },
  loadStories() { console.log('Load stories'); },
  loadLiveStreams() { console.log('Load live streams'); },
  loadAnalytics() { console.log('Load analytics'); },
  loadNotifications() { console.log('Load notifications'); }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = Dashboard;
}
