/**
 * Authentication Check for Dashboard
 * This script must be loaded FIRST before any other scripts
 * It checks if the user is authenticated and redirects to login if not
 */

(function () {
  'use strict';

  // Check if we're on the login page
  const isLoginPage = window.location.pathname.includes('index.html') ||
    window.location.pathname.endsWith('/admin-dashboard/') ||
    window.location.pathname === '/';

  // If on login page, skip auth check
  if (isLoginPage) {
    return;
  }

  // Check for authentication token
  const token = localStorage.getItem('access_token');
  const user = localStorage.getItem('user');

  // If not authenticated, redirect to login
  if (!token || !user) {
    console.log('Not authenticated, redirecting to login...');
    window.location.href = 'index.html';
    return;
  }

  // Optional: Check if token is expired (basic JWT check)
  // DISABLED FOR MOCK API - Uncomment for production with real JWT tokens
  /*
  if (!token.startsWith('mock_')) {
    try {
      const tokenParts = token.split('.');
      if (tokenParts.length === 3) {
        const payload = JSON.parse(atob(tokenParts[1]));
        const exp = payload.exp * 1000; // Convert to milliseconds

        if (Date.now() >= exp) {
          // Token expired, clear storage and redirect
          console.log('Token expired, redirecting to login...');
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('user');
          window.location.href = 'index.html';
          return;
        }
      }
    } catch (e) {
      // Invalid token format, clear storage and redirect
      console.error('Invalid token format:', e);
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
      window.location.href = 'index.html';
      return;
    }
  }
  */

  console.log('Authentication check passed');
})();
