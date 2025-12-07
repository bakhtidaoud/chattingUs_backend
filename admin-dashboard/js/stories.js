/**
 * Stories Management
 * Instagram-style stories with expiration tracking and full-screen viewer
 */

const StoriesManager = {
  currentPage: 1,
  perPage: 20,
  filters: {
    search: '',
    status: 'all',
    mediaType: 'all'
  },
  currentStoryIndex: 0,
  stories: [],
  countdownIntervals: {},

  /**
   * Initialize stories management
   */
  init() {
    this.setupEventListeners();
    this.loadStories();
  },

  /**
   * Setup event listeners
   */
  setupEventListeners() {
    // Search
    const searchInput = document.getElementById('storySearch');
    if (searchInput) {
      searchInput.addEventListener('input', Utils.debounce((e) => {
        this.filters.search = e.target.value;
        this.currentPage = 1;
        this.loadStories();
      }, 300));
    }

    // Filters
    ['storyStatusFilter', 'storyMediaTypeFilter'].forEach(id => {
      const filter = document.getElementById(id);
      if (filter) {
        filter.addEventListener('change', (e) => {
          const filterName = id.replace('story', '').replace('Filter', '').toLowerCase();
          this.filters[filterName] = e.target.value;
          this.currentPage = 1;
          this.loadStories();
        });
      }
    });

    // Add story button
    const addStoryBtn = document.getElementById('addStoryBtn');
    if (addStoryBtn) {
      addStoryBtn.addEventListener('click', () => {
        Modals.open('addStoryModal');
      });
    }

    // Add story form
    const addStoryForm = document.getElementById('addStoryForm');
    if (addStoryForm) {
      addStoryForm.addEventListener('submit', (e) => {
        e.preventDefault();
        this.handleAddStory();
      });
    }

    // Story media upload
    this.setupMediaUpload();

    // Keyboard navigation for story viewer
    document.addEventListener('keydown', (e) => {
      const modal = document.getElementById('storyViewerModal');
      if (modal && modal.classList.contains('active')) {
        if (e.key === 'ArrowLeft') this.previousStory();
        if (e.key === 'ArrowRight') this.nextStory();
        if (e.key === 'Escape') Modals.close('storyViewerModal');
      }
    });
  },

  /**
   * Setup media upload
   */
  setupMediaUpload() {
    const uploadArea = document.getElementById('storyMediaUploadArea');
    const fileInput = document.getElementById('storyMediaInput');
    const preview = document.getElementById('storyMediaPreview');
    const previewMedia = document.getElementById('storyPreviewMedia');
    const removeBtn = document.getElementById('removeStoryMediaBtn');

    if (!uploadArea || !fileInput) return;

    // Click to upload
    uploadArea.addEventListener('click', () => fileInput.click());

    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
      e.preventDefault();
      uploadArea.classList.add('drag-over');
    });

    uploadArea.addEventListener('dragleave', () => {
      uploadArea.classList.remove('drag-over');
    });

    uploadArea.addEventListener('drop', (e) => {
      e.preventDefault();
      uploadArea.classList.remove('drag-over');
      const files = e.dataTransfer.files;
      if (files.length > 0) {
        this.handleMediaSelect(files[0]);
      }
    });

    // File input change
    fileInput.addEventListener('change', (e) => {
      if (e.target.files.length > 0) {
        this.handleMediaSelect(e.target.files[0]);
      }
    });

    // Remove media
    if (removeBtn) {
      removeBtn.addEventListener('click', () => {
        fileInput.value = '';
        preview.style.display = 'none';
        uploadArea.style.display = 'flex';
      });
    }
  },

  /**
   * Handle media selection
   */
  handleMediaSelect(file) {
    if (!file.type.startsWith('image/') && !file.type.startsWith('video/')) {
      Utils.showToast('Please select an image or video file', 'error');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const preview = document.getElementById('storyMediaPreview');
      const previewMedia = document.getElementById('storyPreviewMedia');
      const uploadArea = document.getElementById('storyMediaUploadArea');

      if (file.type.startsWith('video/')) {
        previewMedia.innerHTML = `<video src="${e.target.result}" controls style="width: 100%; border-radius: 8px;"></video>`;
      } else {
        previewMedia.innerHTML = `<img src="${e.target.result}" alt="Preview" style="width: 100%; border-radius: 8px;">`;
      }

      preview.style.display = 'block';
      uploadArea.style.display = 'none';
    };
    reader.readAsDataURL(file);
  },

  /**
   * Load stories
   */
  async loadStories() {
    const container = document.getElementById('storiesContainer');
    if (!container) return;

    container.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i><p>Loading stories...</p></div>';

    // Clear existing countdown intervals
    Object.values(this.countdownIntervals).forEach(interval => clearInterval(interval));
    this.countdownIntervals = {};

    try {
      const params = {
        page: this.currentPage,
        page_size: this.perPage
      };

      if (this.filters.search) params.search = this.filters.search;
      if (this.filters.status !== 'all') {
        params.is_expired = this.filters.status === 'expired';
      }
      if (this.filters.mediaType !== 'all') {
        params.media_type = this.filters.mediaType;
      }

      const response = await API.get('/stories/', params);
      this.stories = response.results || response;

      this.renderStories(this.stories);
      this.renderPagination(response);
    } catch (error) {
      console.error('Error loading stories:', error);
      container.innerHTML = '<p style="text-align: center; padding: 2rem;">Error loading stories</p>';
      Utils.showToast('Failed to load stories', 'error');
    }
  },

  /**
   * Render stories
   */
  renderStories(stories) {
    const container = document.getElementById('storiesContainer');
    if (!container) return;

    if (stories.length === 0) {
      container.innerHTML = '<p style="text-align: center; padding: 2rem;">No stories found</p>';
      return;
    }

    container.innerHTML = stories.map((story, index) => {
      const isExpired = this.isStoryExpired(story);
      const timeRemaining = this.getTimeRemaining(story);

      return `
                <div class="story-card ${isExpired ? 'expired' : ''}" data-story-id="${story.id}">
                    <div class="story-ring ${isExpired ? '' : 'active'}" onclick="StoriesManager.viewStory(${index})">
                        <div class="story-avatar">
                            <img src="${story.user?.profile_picture || `https://ui-avatars.com/api/?name=${encodeURIComponent(story.user?.username || 'User')}`}" 
                                 alt="${story.user?.username}">
                        </div>
                        <div class="story-thumbnail">
                            ${story.media_type === 'video' ?
          `<video src="${story.media_url}" muted></video>
                                 <i class="fas fa-play-circle video-indicator"></i>` :
          `<img src="${story.media_url}" alt="Story">`
        }
                        </div>
                    </div>
                    <div class="story-info">
                        <h4>${story.user?.username || 'Unknown'}</h4>
                        <div class="story-stats">
                            <span><i class="fas fa-eye"></i> ${story.views_count || 0}</span>
                            ${!isExpired ?
          `<span class="story-countdown" id="countdown-${story.id}">
                                    <i class="fas fa-clock"></i> ${timeRemaining}
                                </span>` :
          `<span class="story-expired"><i class="fas fa-times-circle"></i> Expired</span>`
        }
                        </div>
                        <div class="story-actions">
                            <button class="btn-icon" onclick="StoriesManager.viewStory(${index})" title="View">
                                <i class="fas fa-eye"></i>
                            </button>
                            <button class="btn-icon" onclick="StoriesManager.viewViewers(${story.id})" title="Viewers">
                                <i class="fas fa-users"></i>
                            </button>
                            ${!isExpired ?
          `<button class="btn-icon" onclick="StoriesManager.extendExpiration(${story.id})" title="Extend">
                                    <i class="fas fa-clock"></i>
                                </button>` : ''
        }
                            <button class="btn-icon btn-danger" onclick="StoriesManager.deleteStory(${story.id})" title="Delete">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `;
    }).join('');

    // Start countdown timers for active stories
    stories.forEach(story => {
      if (!this.isStoryExpired(story)) {
        this.startCountdown(story);
      }
    });
  },

  /**
   * Check if story is expired
   */
  isStoryExpired(story) {
    if (!story.expires_at) return false;
    return new Date(story.expires_at) < new Date();
  },

  /**
   * Get time remaining
   */
  getTimeRemaining(story) {
    if (!story.expires_at) return 'No expiration';

    const now = new Date();
    const expiresAt = new Date(story.expires_at);
    const diff = expiresAt - now;

    if (diff <= 0) return 'Expired';

    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((diff % (1000 * 60)) / 1000);

    if (hours > 0) return `${hours}h ${minutes}m`;
    if (minutes > 0) return `${minutes}m ${seconds}s`;
    return `${seconds}s`;
  },

  /**
   * Start countdown timer
   */
  startCountdown(story) {
    const countdownEl = document.getElementById(`countdown-${story.id}`);
    if (!countdownEl) return;

    // Clear existing interval
    if (this.countdownIntervals[story.id]) {
      clearInterval(this.countdownIntervals[story.id]);
    }

    // Update every second
    this.countdownIntervals[story.id] = setInterval(() => {
      const timeRemaining = this.getTimeRemaining(story);
      const icon = countdownEl.querySelector('i');
      countdownEl.textContent = timeRemaining;
      countdownEl.prepend(icon);

      if (timeRemaining === 'Expired') {
        clearInterval(this.countdownIntervals[story.id]);
        this.loadStories(); // Reload to update UI
      }
    }, 1000);
  },

  /**
   * View story in full-screen viewer
   */
  async viewStory(index) {
    this.currentStoryIndex = index;
    const story = this.stories[index];

    Modals.open('storyViewerModal');
    const viewer = document.getElementById('storyViewerContent');

    viewer.innerHTML = `
            <div class="story-viewer-header">
                <div class="story-viewer-progress">
                    ${this.stories.map((_, i) => `
                        <div class="progress-segment ${i === index ? 'active' : i < index ? 'completed' : ''}"></div>
                    `).join('')}
                </div>
                <div class="story-viewer-user">
                    <img src="${story.user?.profile_picture || `https://ui-avatars.com/api/?name=${encodeURIComponent(story.user?.username || 'User')}`}" 
                         alt="${story.user?.username}">
                    <div>
                        <h4>${story.user?.username || 'Unknown'}</h4>
                        <p>${Utils.formatDate(story.created_at)}</p>
                    </div>
                </div>
                <button class="story-viewer-close" onclick="Modals.close('storyViewerModal')">
                    <i class="fas fa-times"></i>
                </button>
            </div>

            <div class="story-viewer-media">
                ${story.media_type === 'video' ?
        `<video src="${story.media_url}" autoplay controls></video>` :
        `<img src="${story.media_url}" alt="Story">`
      }
                ${story.text_overlay ? `<div class="story-text-overlay">${story.text_overlay}</div>` : ''}
            </div>

            <div class="story-viewer-nav">
                <button class="story-nav-btn prev" onclick="StoriesManager.previousStory()" ${index === 0 ? 'disabled' : ''}>
                    <i class="fas fa-chevron-left"></i>
                </button>
                <button class="story-nav-btn next" onclick="StoriesManager.nextStory()" ${index === this.stories.length - 1 ? 'disabled' : ''}>
                    <i class="fas fa-chevron-right"></i>
                </button>
            </div>

            <div class="story-viewer-footer">
                <div class="story-viewer-stats">
                    <span><i class="fas fa-eye"></i> ${story.views_count || 0} views</span>
                    <span><i class="fas fa-comment"></i> ${story.replies_count || 0} replies</span>
                </div>
                <div class="story-viewer-actions">
                    <button class="btn-secondary btn-sm" onclick="StoriesManager.viewViewers(${story.id})">
                        <i class="fas fa-users"></i> View Viewers
                    </button>
                    <button class="btn-secondary btn-sm" onclick="StoriesManager.viewReplies(${story.id})">
                        <i class="fas fa-comment"></i> View Replies
                    </button>
                </div>
            </div>
        `;

    // Mark as viewed (optional)
    try {
      await API.post(`/stories/${story.id}/view/`, {});
    } catch (error) {
      console.error('Error marking story as viewed:', error);
    }
  },

  /**
   * Previous story
   */
  previousStory() {
    if (this.currentStoryIndex > 0) {
      this.viewStory(this.currentStoryIndex - 1);
    }
  },

  /**
   * Next story
   */
  nextStory() {
    if (this.currentStoryIndex < this.stories.length - 1) {
      this.viewStory(this.currentStoryIndex + 1);
    }
  },

  /**
   * View viewers
   */
  async viewViewers(id) {
    Modals.open('storyViewersModal');
    const body = document.getElementById('storyViewersBody');
    body.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i></div>';

    try {
      const viewers = await API.get(`/stories/${id}/views/`);

      if (viewers.length === 0) {
        body.innerHTML = '<p style="text-align: center; padding: 2rem;">No viewers yet</p>';
        return;
      }

      body.innerHTML = `
                <div class="viewers-list">
                    ${viewers.map(viewer => `
                        <div class="viewer-item">
                            <img src="${viewer.user?.profile_picture || `https://ui-avatars.com/api/?name=${encodeURIComponent(viewer.user?.username || 'User')}`}" 
                                 alt="${viewer.user?.username}">
                            <div>
                                <h4>${viewer.user?.username || 'Unknown'}</h4>
                                <p>${Utils.formatDate(viewer.viewed_at)}</p>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
    } catch (error) {
      console.error('Error loading viewers:', error);
      body.innerHTML = '<p style="text-align: center; color: #ef4444;">Error loading viewers</p>';
    }
  },

  /**
   * View replies
   */
  async viewReplies(id) {
    Modals.open('storyRepliesModal');
    const body = document.getElementById('storyRepliesBody');
    body.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i></div>';

    try {
      const replies = await API.get(`/stories/${id}/replies/`);

      if (replies.length === 0) {
        body.innerHTML = '<p style="text-align: center; padding: 2rem;">No replies yet</p>';
        return;
      }

      body.innerHTML = `
                <div class="replies-list">
                    ${replies.map(reply => `
                        <div class="reply-item">
                            <img src="${reply.user?.profile_picture || `https://ui-avatars.com/api/?name=${encodeURIComponent(reply.user?.username || 'User')}`}" 
                                 alt="${reply.user?.username}">
                            <div class="reply-content">
                                <h4>${reply.user?.username || 'Unknown'}</h4>
                                <p>${reply.message}</p>
                                <span>${Utils.formatDate(reply.created_at)}</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
    } catch (error) {
      console.error('Error loading replies:', error);
      body.innerHTML = '<p style="text-align: center; color: #ef4444;">Error loading replies</p>';
    }
  },

  /**
   * Extend expiration
   */
  async extendExpiration(id) {
    const hours = prompt('Extend by how many hours?', '24');
    if (!hours) return;

    try {
      await API.post(`/stories/${id}/extend/`, { hours: parseInt(hours) });
      Utils.showToast('Story expiration extended', 'success');
      this.loadStories();
    } catch (error) {
      console.error('Error extending expiration:', error);
      Utils.showToast('Failed to extend expiration', 'error');
    }
  },

  /**
   * Delete story
   */
  async deleteStory(id) {
    if (!confirm('Are you sure you want to delete this story?')) return;

    try {
      await API.delete(`/stories/${id}/`);
      Utils.showToast('Story deleted successfully', 'success');
      Modals.close('storyViewerModal');
      this.loadStories();
    } catch (error) {
      console.error('Error deleting story:', error);
      Utils.showToast('Failed to delete story', 'error');
    }
  },

  /**
   * Handle add story
   */
  async handleAddStory() {
    const fileInput = document.getElementById('storyMediaInput');
    const textOverlay = document.getElementById('storyTextOverlay').value;
    const duration = document.getElementById('storyDuration').value;
    const userId = document.getElementById('storyUser').value;

    if (!fileInput.files[0]) {
      Utils.showToast('Please select a media file', 'error');
      return;
    }

    if (!userId) {
      Utils.showToast('Please select a user', 'error');
      return;
    }

    const formData = new FormData();
    formData.append('media', fileInput.files[0]);
    formData.append('text_overlay', textOverlay);
    formData.append('duration_hours', duration);
    formData.append('user', userId);

    try {
      await API.post('/stories/', formData);
      Utils.showToast('Story created successfully', 'success');
      Modals.close('addStoryModal');
      document.getElementById('addStoryForm').reset();
      document.getElementById('storyMediaPreview').style.display = 'none';
      document.getElementById('storyMediaUploadArea').style.display = 'flex';
      this.loadStories();
    } catch (error) {
      console.error('Error creating story:', error);
      Utils.showToast('Failed to create story', 'error');
    }
  },

  /**
   * Render pagination
   */
  renderPagination(response) {
    const pagination = document.getElementById('storiesPagination');
    if (!pagination || !response.count) return;

    const totalPages = Math.ceil(response.count / this.perPage);
    if (totalPages <= 1) {
      pagination.innerHTML = '';
      return;
    }

    let html = '<div class="pagination">';

    html += `<button class="pagination-btn" ${this.currentPage === 1 ? 'disabled' : ''} 
                 onclick="StoriesManager.goToPage(${this.currentPage - 1})">
                 <i class="fas fa-chevron-left"></i>
                 </button>`;

    for (let i = 1; i <= Math.min(totalPages, 5); i++) {
      html += `<button class="pagination-btn ${i === this.currentPage ? 'active' : ''}" 
                     onclick="StoriesManager.goToPage(${i})">${i}</button>`;
    }

    html += `<button class="pagination-btn" ${this.currentPage === totalPages ? 'disabled' : ''} 
                 onclick="StoriesManager.goToPage(${this.currentPage + 1})">
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
    this.loadStories();
  },

  /**
   * Cleanup on destroy
   */
  destroy() {
    Object.values(this.countdownIntervals).forEach(interval => clearInterval(interval));
    this.countdownIntervals = {};
  }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
  module.exports = StoriesManager;
}
