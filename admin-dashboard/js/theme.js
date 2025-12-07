/**
 * Dark Mode Manager
 * Handles theme switching and persistence
 */

const ThemeManager = {
  currentTheme: 'light',
  storageKey: 'admin-dashboard-theme',

  /**
   * Initialize theme manager
   */
  init() {
    this.loadTheme();
    this.setupToggle();
    this.detectSystemPreference();
  },

  /**
   * Load theme from localStorage or system preference
   */
  loadTheme() {
    // Check localStorage first
    const savedTheme = localStorage.getItem(this.storageKey);

    if (savedTheme) {
      this.setTheme(savedTheme);
    } else {
      // Check system preference
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      this.setTheme(prefersDark ? 'dark' : 'light');
    }
  },

  /**
   * Set theme
   */
  setTheme(theme) {
    this.currentTheme = theme;
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(this.storageKey, theme);

    // Update toggle button
    this.updateToggleButton();

    // Update Chart.js themes if charts exist
    this.updateChartThemes();

    // Dispatch event for other components
    window.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme } }));
  },

  /**
   * Toggle theme
   */
  toggleTheme() {
    const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
    this.setTheme(newTheme);
  },

  /**
   * Setup toggle button
   */
  setupToggle() {
    const toggleBtn = document.getElementById('themeToggle');
    if (toggleBtn) {
      toggleBtn.addEventListener('click', () => this.toggleTheme());
    }

    // Also support keyboard shortcut (Ctrl/Cmd + Shift + D)
    document.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'D') {
        e.preventDefault();
        this.toggleTheme();
      }
    });
  },

  /**
   * Update toggle button appearance
   */
  updateToggleButton() {
    const toggleBtn = document.getElementById('themeToggle');
    if (!toggleBtn) return;

    const slider = toggleBtn.querySelector('.theme-toggle-slider');
    if (slider) {
      slider.innerHTML = this.currentTheme === 'dark'
        ? '<i class="fas fa-moon"></i>'
        : '<i class="fas fa-sun"></i>';
    }
  },

  /**
   * Detect system preference changes
   */
  detectSystemPreference() {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

    mediaQuery.addEventListener('change', (e) => {
      // Only auto-switch if user hasn't manually set a preference
      if (!localStorage.getItem(this.storageKey)) {
        this.setTheme(e.matches ? 'dark' : 'light');
      }
    });
  },

  /**
   * Update Chart.js themes
   */
  updateChartThemes() {
    if (typeof Chart === 'undefined') return;

    const isDark = this.currentTheme === 'dark';

    // Update Chart.js defaults
    Chart.defaults.color = isDark ? '#a0aec0' : '#718096';
    Chart.defaults.borderColor = isDark ? '#4a5568' : '#e2e8f0';

    // Update all existing charts
    Object.values(Chart.instances).forEach(chart => {
      if (chart.options.scales) {
        // Update scales
        Object.values(chart.options.scales).forEach(scale => {
          if (scale.grid) {
            scale.grid.color = isDark ? '#4a5568' : '#e2e8f0';
          }
          if (scale.ticks) {
            scale.ticks.color = isDark ? '#a0aec0' : '#718096';
          }
        });
      }

      // Update legend
      if (chart.options.plugins && chart.options.plugins.legend) {
        chart.options.plugins.legend.labels.color = isDark ? '#e2e8f0' : '#2d3748';
      }

      chart.update();
    });
  },

  /**
   * Get current theme
   */
  getTheme() {
    return this.currentTheme;
  },

  /**
   * Check if dark mode is active
   */
  isDarkMode() {
    return this.currentTheme === 'dark';
  }
};

// Initialize on DOM load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => ThemeManager.init());
} else {
  ThemeManager.init();
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ThemeManager;
}
