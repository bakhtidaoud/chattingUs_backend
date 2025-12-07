/**
 * Settings Management
 * System configuration and settings
 */

const SettingsManager = {
  currentTab: 'general',
  settings: {},
  hasUnsavedChanges: false,

  /**
   * Initialize settings management
   */
  init() {
    this.setupEventListeners();
    this.loadSettings();
  },

  /**
   * Setup event listeners
   */
  setupEventListeners() {
    // Settings tabs
    document.querySelectorAll('.settings-tab').forEach(tab => {
      tab.addEventListener('click', (e) => {
        const tabName = e.target.dataset.tab;
        this.switchTab(tabName);
      });
    });

    // Save button
    const saveBtn = document.getElementById('saveSettingsBtn');
    if (saveBtn) {
      saveBtn.addEventListener('click', () => this.saveSettings());
    }

    // Cancel button
    const cancelBtn = document.getElementById('cancelSettingsBtn');
    if (cancelBtn) {
      cancelBtn.addEventListener('click', () => this.cancelChanges());
    }

    // Test email button
    const testEmailBtn = document.getElementById('testEmailBtn');
    if (testEmailBtn) {
      testEmailBtn.addEventListener('click', () => this.testEmail());
    }

    // Logo upload
    const logoInput = document.getElementById('logoUpload');
    if (logoInput) {
      logoInput.addEventListener('change', (e) => this.handleLogoUpload(e));
    }

    // Favicon upload
    const faviconInput = document.getElementById('faviconUpload');
    if (faviconInput) {
      faviconInput.addEventListener('change', (e) => this.handleFaviconUpload(e));
    }

    // Track changes
    document.querySelectorAll('.settings-form input, .settings-form textarea, .settings-form select').forEach(input => {
      input.addEventListener('change', () => {
        this.hasUnsavedChanges = true;
        this.updateSaveButton();
      });
    });

    // Warn before leaving with unsaved changes
    window.addEventListener('beforeunload', (e) => {
      if (this.hasUnsavedChanges) {
        e.preventDefault();
        e.returnValue = '';
      }
    });
  },

  /**
   * Switch tab
   */
  switchTab(tabName) {
    this.currentTab = tabName;

    // Update active tab
    document.querySelectorAll('.settings-tab').forEach(tab => {
      tab.classList.toggle('active', tab.dataset.tab === tabName);
    });

    // Hide all panels
    document.querySelectorAll('.settings-panel').forEach(panel => {
      panel.style.display = 'none';
    });

    // Show selected panel
    const selectedPanel = document.getElementById(`${tabName}Settings`);
    if (selectedPanel) {
      selectedPanel.style.display = 'block';
    }
  },

  /**
   * Load settings
   */
  async loadSettings() {
    try {
      this.settings = await API.get('/settings/');
      this.populateSettings();
    } catch (error) {
      console.error('Error loading settings:', error);
      Utils.showToast('Failed to load settings', 'error');
    }
  },

  /**
   * Populate settings form
   */
  populateSettings() {
    // General settings
    this.setFieldValue('siteName', this.settings.site_name);
    this.setFieldValue('siteDescription', this.settings.site_description);
    this.setFieldValue('contactEmail', this.settings.contact_email);
    this.setFieldValue('supportEmail', this.settings.support_email);

    if (this.settings.logo_url) {
      this.displayImage('logoPreview', this.settings.logo_url);
    }
    if (this.settings.favicon_url) {
      this.displayImage('faviconPreview', this.settings.favicon_url);
    }

    // Email settings
    this.setFieldValue('emailBackend', this.settings.email_backend);
    this.setFieldValue('smtpHost', this.settings.smtp_host);
    this.setFieldValue('smtpPort', this.settings.smtp_port);
    this.setFieldValue('emailUsername', this.settings.email_username);
    this.setFieldValue('emailPassword', this.settings.email_password);

    // Media settings
    this.setFieldValue('maxFileSize', this.settings.max_file_size);
    this.setFieldValue('allowedFileTypes', this.settings.allowed_file_types);
    this.setFieldValue('storageBackend', this.settings.storage_backend);
    this.setFieldValue('cdnUrl', this.settings.cdn_url);

    // Security settings
    this.setFieldValue('jwtLifetime', this.settings.jwt_lifetime);
    this.setFieldValue('minPasswordLength', this.settings.min_password_length);
    this.setFieldValue('requireUppercase', this.settings.require_uppercase);
    this.setFieldValue('requireNumbers', this.settings.require_numbers);
    this.setFieldValue('requireSpecialChars', this.settings.require_special_chars);
    this.setFieldValue('enforce2FA', this.settings.enforce_2fa);
    this.setFieldValue('sessionTimeout', this.settings.session_timeout);
    this.setFieldValue('corsOrigins', this.settings.cors_origins);

    // Notification settings
    this.setFieldValue('firebaseServerKey', this.settings.firebase_server_key);
    this.setFieldValue('pushEnabled', this.settings.push_enabled);
    this.setFieldValue('emailNotificationsEnabled', this.settings.email_notifications_enabled);
    this.setFieldValue('notificationFrequency', this.settings.notification_frequency);

    // Moderation settings
    this.setFieldValue('autoModeration', this.settings.auto_moderation);
    this.setFieldValue('bannedWords', this.settings.banned_words);
    this.setFieldValue('contentFilters', this.settings.content_filters);
    this.setFieldValue('reportThreshold', this.settings.report_threshold);

    // API settings
    this.setFieldValue('apiRateLimit', this.settings.api_rate_limit);
    this.setFieldValue('paginationSize', this.settings.pagination_size);
    this.setFieldValue('apiDocsUrl', this.settings.api_docs_url);

    this.hasUnsavedChanges = false;
    this.updateSaveButton();
  },

  /**
   * Set field value
   */
  setFieldValue(fieldId, value) {
    const field = document.getElementById(fieldId);
    if (!field) return;

    if (field.type === 'checkbox') {
      field.checked = value;
    } else {
      field.value = value || '';
    }
  },

  /**
   * Get field value
   */
  getFieldValue(fieldId) {
    const field = document.getElementById(fieldId);
    if (!field) return null;

    if (field.type === 'checkbox') {
      return field.checked;
    }
    return field.value;
  },

  /**
   * Display image preview
   */
  displayImage(previewId, url) {
    const preview = document.getElementById(previewId);
    if (preview) {
      preview.innerHTML = `<img src="${url}" alt="Preview">`;
    }
  },

  /**
   * Handle logo upload
   */
  handleLogoUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      this.displayImage('logoPreview', event.target.result);
      this.hasUnsavedChanges = true;
      this.updateSaveButton();
    };
    reader.readAsDataURL(file);
  },

  /**
   * Handle favicon upload
   */
  handleFaviconUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      this.displayImage('faviconPreview', event.target.result);
      this.hasUnsavedChanges = true;
      this.updateSaveButton();
    };
    reader.readAsDataURL(file);
  },

  /**
   * Save settings
   */
  async saveSettings() {
    const formData = new FormData();

    // General settings
    formData.append('site_name', this.getFieldValue('siteName'));
    formData.append('site_description', this.getFieldValue('siteDescription'));
    formData.append('contact_email', this.getFieldValue('contactEmail'));
    formData.append('support_email', this.getFieldValue('supportEmail'));

    // Logo and favicon
    const logoInput = document.getElementById('logoUpload');
    if (logoInput && logoInput.files[0]) {
      formData.append('logo', logoInput.files[0]);
    }

    const faviconInput = document.getElementById('faviconUpload');
    if (faviconInput && faviconInput.files[0]) {
      formData.append('favicon', faviconInput.files[0]);
    }

    // Email settings
    formData.append('email_backend', this.getFieldValue('emailBackend'));
    formData.append('smtp_host', this.getFieldValue('smtpHost'));
    formData.append('smtp_port', this.getFieldValue('smtpPort'));
    formData.append('email_username', this.getFieldValue('emailUsername'));
    formData.append('email_password', this.getFieldValue('emailPassword'));

    // Media settings
    formData.append('max_file_size', this.getFieldValue('maxFileSize'));
    formData.append('allowed_file_types', this.getFieldValue('allowedFileTypes'));
    formData.append('storage_backend', this.getFieldValue('storageBackend'));
    formData.append('cdn_url', this.getFieldValue('cdnUrl'));

    // Security settings
    formData.append('jwt_lifetime', this.getFieldValue('jwtLifetime'));
    formData.append('min_password_length', this.getFieldValue('minPasswordLength'));
    formData.append('require_uppercase', this.getFieldValue('requireUppercase'));
    formData.append('require_numbers', this.getFieldValue('requireNumbers'));
    formData.append('require_special_chars', this.getFieldValue('requireSpecialChars'));
    formData.append('enforce_2fa', this.getFieldValue('enforce2FA'));
    formData.append('session_timeout', this.getFieldValue('sessionTimeout'));
    formData.append('cors_origins', this.getFieldValue('corsOrigins'));

    // Notification settings
    formData.append('firebase_server_key', this.getFieldValue('firebaseServerKey'));
    formData.append('push_enabled', this.getFieldValue('pushEnabled'));
    formData.append('email_notifications_enabled', this.getFieldValue('emailNotificationsEnabled'));
    formData.append('notification_frequency', this.getFieldValue('notificationFrequency'));

    // Moderation settings
    formData.append('auto_moderation', this.getFieldValue('autoModeration'));
    formData.append('banned_words', this.getFieldValue('bannedWords'));
    formData.append('content_filters', this.getFieldValue('contentFilters'));
    formData.append('report_threshold', this.getFieldValue('reportThreshold'));

    // API settings
    formData.append('api_rate_limit', this.getFieldValue('apiRateLimit'));
    formData.append('pagination_size', this.getFieldValue('paginationSize'));
    formData.append('api_docs_url', this.getFieldValue('apiDocsUrl'));

    try {
      await API.put('/settings/', formData);
      Utils.showToast('Settings saved successfully', 'success');
      this.hasUnsavedChanges = false;
      this.updateSaveButton();
      this.loadSettings(); // Reload to get updated values
    } catch (error) {
      console.error('Error saving settings:', error);
      Utils.showToast('Failed to save settings', 'error');
    }
  },

  /**
   * Cancel changes
   */
  cancelChanges() {
    if (this.hasUnsavedChanges) {
      if (!confirm('You have unsaved changes. Are you sure you want to cancel?')) {
        return;
      }
    }

    this.loadSettings();
    this.hasUnsavedChanges = false;
    this.updateSaveButton();
  },

  /**
   * Update save button state
   */
  updateSaveButton() {
    const saveBtn = document.getElementById('saveSettingsBtn');
    if (saveBtn) {
      saveBtn.disabled = !this.hasUnsavedChanges;
    }
  },

  /**
   * Test email
   */
  async testEmail() {
    const testEmailAddress = prompt('Enter email address to send test email:');
    if (!testEmailAddress) return;

    try {
      await API.post('/settings/test-email/', {
        email: testEmailAddress,
        smtp_host: this.getFieldValue('smtpHost'),
        smtp_port: this.getFieldValue('smtpPort'),
        email_username: this.getFieldValue('emailUsername'),
        email_password: this.getFieldValue('emailPassword')
      });
      Utils.showToast('Test email sent successfully', 'success');
    } catch (error) {
      console.error('Error sending test email:', error);
      Utils.showToast('Failed to send test email', 'error');
    }
  }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
  module.exports = SettingsManager;
}
