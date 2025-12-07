/**
 * ChattingUs Admin Dashboard - Authentication
 * Handles login, logout, and authentication state
 */

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  Auth.init();
});

const Auth = {
  /**
   * Initialize authentication
   */
  init() {
    // Initialize theme
    Utils.initTheme();

    // Check if on login page
    if (window.location.pathname.includes('index.html') ||
      window.location.pathname === '/' ||
      window.location.pathname.endsWith('/admin-dashboard/')) {
      this.initLoginPage();
    } else {
      // Require authentication for other pages
      Utils.requireAuth();
    }
  },

  /**
   * Initialize login page
   */
  initLoginPage() {
    // Redirect if already authenticated
    Utils.redirectIfAuthenticated();

    // Get form elements
    const loginForm = document.getElementById('loginForm');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const togglePassword = document.getElementById('togglePassword');
    const themeToggle = document.getElementById('themeToggle');

    // Form submission
    if (loginForm) {
      loginForm.addEventListener('submit', (e) => {
        e.preventDefault();
        this.handleLogin();
      });
    }

    // Toggle password visibility
    if (togglePassword) {
      togglePassword.addEventListener('click', () => {
        const type = passwordInput.type === 'password' ? 'text' : 'password';
        passwordInput.type = type;

        const icon = togglePassword.querySelector('i');
        icon.classList.toggle('fa-eye');
        icon.classList.toggle('fa-eye-slash');
      });
    }

    // Theme toggle
    if (themeToggle) {
      themeToggle.addEventListener('click', () => {
        Utils.toggleTheme();
      });
    }

    // Clear any error messages on input
    [emailInput, passwordInput].forEach(input => {
      if (input) {
        input.addEventListener('input', () => {
          Utils.hideError();
        });
      }
    });

    // Auto-focus email input
    if (emailInput) {
      emailInput.focus();
    }
  },

  /**
   * Handle login form submission
   */
  async handleLogin() {
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const rememberMe = document.getElementById('rememberMe');
    const loginButton = document.getElementById('loginButton');

    const email = emailInput.value.trim();
    const password = passwordInput.value;

    // Validate inputs
    if (!email || !password) {
      Utils.showError('Please enter both email and password');
      return;
    }

    if (!Utils.validateEmail(email)) {
      Utils.showError('Please enter a valid email address');
      emailInput.focus();
      return;
    }

    const passwordValidation = Utils.validatePassword(password);
    if (!passwordValidation.valid) {
      Utils.showError(passwordValidation.message);
      passwordInput.focus();
      return;
    }

    // Show loading state
    Utils.setButtonLoading(loginButton, true);
    Utils.hideError();

    try {
      // Call login API
      const response = await API.login(email, password);

      // Store tokens
      if (response.access) {
        localStorage.setItem('access_token', response.access);
      }
      if (response.refresh) {
        localStorage.setItem('refresh_token', response.refresh);
      }

      // Store user data
      if (response.user) {
        localStorage.setItem('user', JSON.stringify(response.user));
      }

      // Store remember me preference
      if (rememberMe && rememberMe.checked) {
        localStorage.setItem('remember_me', 'true');
      }

      // Show success message
      Utils.showToast('Login successful! Redirecting...', 'success');

      // Redirect to dashboard after short delay
      setTimeout(() => {
        window.location.href = 'dashboard.html';
      }, 1000);

    } catch (error) {
      console.error('Login error:', error);

      // Show error message
      let errorMessage = 'Login failed. Please try again.';

      if (error.message.includes('Invalid credentials') ||
        error.message.includes('401')) {
        errorMessage = 'Invalid email or password';
      } else if (error.message.includes('Network') ||
        error.message.includes('Failed to fetch')) {
        errorMessage = 'Network error. Please check your connection.';
      } else if (error.message) {
        errorMessage = error.message;
      }

      Utils.showError(errorMessage);

      // Reset loading state
      Utils.setButtonLoading(loginButton, false);
    }
  },

  /**
   * Handle logout
   */
  async logout() {
    try {
      // Call logout API
      await API.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear local storage
      this.clearAuthData();

      // Redirect to login
      window.location.href = 'index.html';
    }
  },

  /**
   * Clear authentication data
   */
  clearAuthData() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    localStorage.removeItem('remember_me');
  },

  /**
   * Get current user
   * @returns {object|null}
   */
  getCurrentUser() {
    const userStr = localStorage.getItem('user');
    if (!userStr) return null;

    try {
      return JSON.parse(userStr);
    } catch (e) {
      return null;
    }
  },

  /**
   * Check if user is admin
   * @returns {boolean}
   */
  isAdmin() {
    const user = this.getCurrentUser();
    return user && (user.is_staff || user.is_superuser);
  },

  /**
   * Refresh access token
   * @returns {Promise<boolean>}
   */
  async refreshAccessToken() {
    const refreshToken = localStorage.getItem('refresh_token');

    if (!refreshToken) {
      return false;
    }

    try {
      const response = await API.refreshToken(refreshToken);

      if (response.access) {
        localStorage.setItem('access_token', response.access);
        return true;
      }

      return false;
    } catch (error) {
      console.error('Token refresh error:', error);
      this.clearAuthData();
      window.location.href = 'index.html';
      return false;
    }
  },

  /**
   * Check token expiration and refresh if needed
   */
  async checkTokenExpiration() {
    const token = localStorage.getItem('access_token');

    if (!token) {
      return false;
    }

    if (Utils.isTokenExpired(token)) {
      return await this.refreshAccessToken();
    }

    return true;
  }
};

// Set up token refresh interval (every 4 minutes)
if (Utils.isAuthenticated()) {
  setInterval(() => {
    Auth.checkTokenExpiration();
  }, 4 * 60 * 1000);
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = Auth;
}
