/**
 * API Integration Layer
 * Handles all HTTP requests to the backend API
 */

const API = {
  // Base configuration
  baseURL: 'http://localhost:8000/api',
  timeout: 30000,
  retryAttempts: 3,
  retryDelay: 1000,

  /**
   * Get default headers
   */
  getHeaders() {
    const headers = {
      'Content-Type': 'application/json',
    };

    const token = localStorage.getItem('access_token');
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    return headers;
  },

  /**
   * Make HTTP request
   */
  async request(method, endpoint, data = null, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const headers = options.headers || this.getHeaders();

    // Handle FormData
    if (data instanceof FormData) {
      delete headers['Content-Type'];
    }

    const config = {
      method,
      headers,
      ...options
    };

    if (data && method !== 'GET') {
      config.body = data instanceof FormData ? data : JSON.stringify(data);
    }

    // Add query parameters for GET requests
    if (data && method === 'GET') {
      const params = new URLSearchParams(data);
      const queryString = params.toString();
      return this.fetchWithRetry(`${url}?${queryString}`, config);
    }

    return this.fetchWithRetry(url, config);
  },

  /**
   * Fetch with retry logic
   */
  async fetchWithRetry(url, config, attempt = 1) {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);

      const response = await fetch(url, {
        ...config,
        signal: controller.signal
      });

      clearTimeout(timeoutId);

      return await this.handleResponse(response);
    } catch (error) {
      if (attempt < this.retryAttempts && this.shouldRetry(error)) {
        await this.delay(this.retryDelay * attempt);
        return this.fetchWithRetry(url, config, attempt + 1);
      }
      throw this.handleError(error);
    }
  },

  /**
   * Handle response
   */
  async handleResponse(response) {
    // Handle 401 Unauthorized
    // DISABLED: Don't auto-redirect on 401 to prevent logout when API endpoints don't exist
    /*
    if (response.status === 401) {
      const refreshed = await this.tryRefreshToken();
      if (!refreshed) {
        this.redirectToLogin();
        throw new Error('Authentication required');
      }
      // Retry the original request will happen automatically
      throw new Error('Token refreshed, retry needed');
    }
    */

    // Just throw error on 401 without redirecting
    if (response.status === 401) {
      throw {
        status: 401,
        message: 'Unauthorized - API endpoint may not exist or require authentication',
        errors: {}
      };
    }

    // Handle other error status codes
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw {
        status: response.status,
        message: error.message || error.detail || this.getStatusMessage(response.status),
        errors: error.errors || {}
      };
    }

    // Handle empty responses
    if (response.status === 204) {
      return null;
    }

    return await response.json();
  },

  /**
   * Handle errors
   */
  handleError(error) {
    if (error.name === 'AbortError') {
      return { message: 'Request timeout', status: 408 };
    }

    if (!navigator.onLine) {
      return { message: 'No internet connection', status: 0 };
    }

    return error;
  },

  /**
   * Should retry request
   */
  shouldRetry(error) {
    return error.status === 408 || error.status === 0 || error.status >= 500;
  },

  /**
   * Get status message
   */
  getStatusMessage(status) {
    const messages = {
      400: 'Bad request',
      401: 'Unauthorized',
      403: 'Permission denied',
      404: 'Not found',
      408: 'Request timeout',
      500: 'Server error',
      502: 'Bad gateway',
      503: 'Service unavailable'
    };
    return messages[status] || 'An error occurred';
  },

  /**
   * Delay helper
   */
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  },

  /**
   * Try to refresh token
   */
  async tryRefreshToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) return false;

    try {
      const response = await fetch(`${this.baseURL}/auth/token/refresh/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh: refreshToken })
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('access_token', data.access);
        return true;
      }
    } catch (error) {
      console.error('Token refresh failed:', error);
    }

    return false;
  },

  /**
   * Redirect to login
   */
  redirectToLogin() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/admin-dashboard/index.html';
  },

  // Convenience methods
  get(endpoint, params) {
    return this.request('GET', endpoint, params);
  },

  post(endpoint, data) {
    return this.request('POST', endpoint, data);
  },

  put(endpoint, data) {
    return this.request('PUT', endpoint, data);
  },

  patch(endpoint, data) {
    return this.request('PATCH', endpoint, data);
  },

  delete(endpoint) {
    return this.request('DELETE', endpoint);
  },

  // Shortcut methods for commonly used endpoints
  getDashboardStats() {
    return this.analytics.getDashboardStats();
  },

  getUsers(params) {
    return this.users.getUsers(params);
  },

  getUser(id) {
    return this.users.getUser(id);
  },

  verifyUser(id) {
    return this.post(`/users/${id}/verify/`, {});
  },

  updateUser(id, data) {
    return this.users.updateUser(id, data);
  },

  getPosts(params) {
    return this.posts.getPosts(params);
  },

  getPost(id) {
    return this.posts.getPost(id);
  },

  getStories(params) {
    return this.stories.getStories(params);
  },

  getReels(params) {
    return this.reels.getReels(params);
  },

  login(email, password) {
    return this.auth.login(email, password);
  },

  logout() {
    return this.auth.logout();
  },

  // ============================================
  // AUTHENTICATION API
  // ============================================

  auth: {
    login(email, password, rememberMe = false) {
      return API.post('/auth/login/', { email, password, remember_me: rememberMe });
    },

    logout() {
      const refreshToken = localStorage.getItem('refresh_token');
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      return API.post('/auth/logout/', { refresh: refreshToken });
    },

    refreshToken() {
      const refreshToken = localStorage.getItem('refresh_token');
      return API.post('/auth/token/refresh/', { refresh: refreshToken });
    },

    getCurrentUser() {
      return API.get('/auth/me/');
    }
  },

  // ============================================
  // USERS API
  // ============================================

  users: {
    getUsers(params = {}) {
      return API.get('/users/', params);
    },

    getUser(id) {
      return API.get(`/users/${id}/`);
    },

    createUser(data) {
      return API.post('/users/', data);
    },

    updateUser(id, data) {
      return API.put(`/users/${id}/`, data);
    },

    deleteUser(id) {
      return API.delete(`/users/${id}/`);
    },

    banUser(id, reason) {
      return API.post(`/users/${id}/ban/`, { reason });
    },

    unbanUser(id) {
      return API.post(`/users/${id}/unban/`);
    },

    verifyEmail(id) {
      return API.post(`/users/${id}/verify-email/`);
    },

    lockAccount(id) {
      return API.post(`/users/${id}/lock/`);
    },

    unlockAccount(id) {
      return API.post(`/users/${id}/unlock/`);
    },

    exportUsers(filters = {}) {
      return API.get('/users/export/', filters);
    }
  },

  // ============================================
  // POSTS API
  // ============================================

  posts: {
    getPosts(params = {}) {
      return API.get('/posts/', params);
    },

    getPost(id) {
      return API.get(`/posts/${id}/`);
    },

    createPost(data) {
      return API.post('/posts/', data);
    },

    updatePost(id, data) {
      return API.put(`/posts/${id}/`, data);
    },

    deletePost(id) {
      return API.delete(`/posts/${id}/`);
    },

    archivePost(id) {
      return API.post(`/posts/${id}/archive/`);
    },

    unarchivePost(id) {
      return API.post(`/posts/${id}/unarchive/`);
    },

    getComments(id) {
      return API.get(`/posts/${id}/comments/`);
    },

    getLikes(id) {
      return API.get(`/posts/${id}/likes/`);
    }
  },

  // ============================================
  // STORIES API
  // ============================================

  stories: {
    getStories(params = {}) {
      return API.get('/stories/', params);
    },

    getStory(id) {
      return API.get(`/stories/${id}/`);
    },

    createStory(data) {
      return API.post('/stories/', data);
    },

    deleteStory(id) {
      return API.delete(`/stories/${id}/`);
    },

    getViews(id) {
      return API.get(`/stories/${id}/views/`);
    },

    getReplies(id) {
      return API.get(`/stories/${id}/replies/`);
    },

    extendExpiration(id, hours) {
      return API.post(`/stories/${id}/extend/`, { hours });
    },

    getHighlights() {
      return API.get('/stories/highlights/');
    }
  },

  // ============================================
  // REELS API
  // ============================================

  reels: {
    getReels(params = {}) {
      return API.get('/reels/', params);
    },

    getReel(id) {
      return API.get(`/reels/${id}/`);
    },

    createReel(data) {
      return API.post('/reels/', data);
    },

    updateReel(id, data) {
      return API.put(`/reels/${id}/`, data);
    },

    deleteReel(id) {
      return API.delete(`/reels/${id}/`);
    },

    getComments(id) {
      return API.get(`/reels/${id}/comments/`);
    },

    getLikes(id) {
      return API.get(`/reels/${id}/likes/`);
    },

    markViewed(id) {
      return API.post(`/reels/${id}/view/`);
    }
  },

  // ============================================
  // CHAT API
  // ============================================

  chat: {
    getChats(params = {}) {
      return API.get('/chat/chats/', params);
    },

    getChat(id) {
      return API.get(`/chat/chats/${id}/`);
    },

    getMessages(id, params = {}) {
      return API.get(`/chat/chats/${id}/messages/`, params);
    },

    deleteMessage(id) {
      return API.delete(`/chat/messages/${id}/`);
    },

    deleteChat(id) {
      return API.delete(`/chat/chats/${id}/`);
    },

    exportChat(id) {
      return API.get(`/chat/chats/${id}/export/`);
    }
  },

  // ============================================
  // LIVE STREAMS API
  // ============================================

  live: {
    getStreams(params = {}) {
      return API.get('/live/streams/', params);
    },

    getStream(id) {
      return API.get(`/live/streams/${id}/`);
    },

    endStream(id) {
      return API.post(`/live/streams/${id}/end/`);
    },

    deleteStream(id) {
      return API.delete(`/live/streams/${id}/`);
    },

    getViewers(id) {
      return API.get(`/live/streams/${id}/viewers/`);
    },

    getComments(id) {
      return API.get(`/live/streams/${id}/comments/`);
    },

    getReactions(id) {
      return API.get(`/live/streams/${id}/reactions/`);
    },

    getStatistics() {
      return API.get('/live/streams/stats/');
    }
  },

  // ============================================
  // NOTIFICATIONS API
  // ============================================

  notifications: {
    getNotifications(params = {}) {
      return API.get('/notifications/', params);
    },

    getNotification(id) {
      return API.get(`/notifications/${id}/`);
    },

    markAsRead(id) {
      return API.put(`/notifications/${id}/mark-read/`, { is_read: true });
    },

    deleteNotification(id) {
      return API.delete(`/notifications/${id}/`);
    },

    getStatistics() {
      return API.get('/notifications/statistics/');
    },

    getPreferences(userId) {
      return API.get(`/notifications/preferences/${userId}/`);
    },

    updatePreferences(userId, data) {
      return API.put(`/notifications/preferences/${userId}/`, data);
    }
  },

  // ============================================
  // MODERATION & REPORTS API
  // ============================================

  moderation: {
    getReports(params = {}) {
      return API.get('/moderation/reports/', params);
    },

    getReport(id) {
      return API.get(`/moderation/reports/${id}/`);
    },

    updateReport(id, data) {
      return API.put(`/moderation/reports/${id}/`, data);
    },

    createAction(data) {
      return API.post('/moderation/actions/', data);
    },

    getActions(params = {}) {
      return API.get('/moderation/actions/', params);
    },

    getStatistics() {
      return API.get('/moderation/reports/statistics/');
    }
  },

  // ============================================
  // SECURITY API
  // ============================================

  security: {
    getOverview() {
      return API.get('/security/overview/');
    },

    get2FAUsers() {
      return API.get('/security/2fa/users/');
    },

    reset2FA(userId) {
      return API.post(`/security/2fa/${userId}/reset/`);
    },

    getFailedLogins(params = {}) {
      return API.get('/security/failed-logins/', params);
    },

    getSessions(params = {}) {
      return API.get('/security/sessions/', params);
    },

    terminateSession(sessionId) {
      return API.delete(`/security/sessions/${sessionId}/`);
    },

    getLogs(params = {}) {
      return API.get('/security/logs/', params);
    },

    exportLogs() {
      return API.get('/security/logs/export/');
    },

    getBlacklist(params = {}) {
      return API.get('/security/blacklist/', params);
    },

    addToBlacklist(data) {
      return API.post('/security/blacklist/', data);
    },

    removeFromBlacklist(ipAddress) {
      return API.delete(`/security/blacklist/${ipAddress}/`);
    }
  },

  // ============================================
  // SETTINGS API
  // ============================================

  settings: {
    getSettings() {
      return API.get('/settings/');
    },

    updateSettings(data) {
      return API.put('/settings/', data);
    },

    testEmail(data) {
      return API.post('/settings/test-email/', data);
    }
  },

  // ============================================
  // ANALYTICS API
  // ============================================

  analytics: {
    getDashboardStats() {
      return API.get('/analytics/dashboard/');
    },

    getUserGrowth(params = {}) {
      return API.get('/analytics/users/growth/', params);
    },

    getContentActivity(params = {}) {
      return API.get('/analytics/content/activity/', params);
    },

    getRecentActivity(params = {}) {
      return API.get('/analytics/activity/recent/', params);
    }
  }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = API;
}
