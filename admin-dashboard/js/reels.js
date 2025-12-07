/**
 * Reels Management
 * TikTok-style reels with video playback and analytics
 */

const ReelsManager = {
  currentPage: 1,
  perPage: 20,
  filters: {
    search: '',
    user: 'all',
    sortBy: 'recent'
  },
  currentReelIndex: 0,
  reels: [],

  /**
   * Initialize reels management
   */
  init() {
    this.setupEventListeners();
    this.loadReels();
  },

  /**
   * Setup event listeners
   */
  setupEventListeners() {
    // Search
    const searchInput = document.getElementById('reelSearch');
    if (searchInput) {
      searchInput.addEventListener('input', Utils.debounce((e) => {
        this.filters.search = e.target.value;
        this.currentPage = 1;
        this.loadReels();
      }, 300));
    }

    // Filters
    ['reelUserFilter', 'reelSortFilter'].forEach(id => {
      const filter = document.getElementById(id);
      if (filter) {
        filter.addEventListener('change', (e) => {
          const filterName = id.replace('reel', '').replace('Filter', '').toLowerCase();
          this.filters[filterName] = e.target.value;
          this.currentPage = 1;
          this.loadReels();
        });
      }
    });

    // Add reel button
    const addReelBtn = document.getElementById('addReelBtn');
    if (addReelBtn) {
      addReelBtn.addEventListener('click', () => {
        Modals.open('addReelModal');
      });
    }

    // Add reel form
    const addReelForm = document.getElementById('addReelForm');
    if (addReelForm) {
      addReelForm.addEventListener('submit', (e) => {
        e.preventDefault();
        this.handleAddReel();
      });
    }

    // Edit reel form
    const editReelForm = document.getElementById('editReelForm');
    if (editReelForm) {
      editReelForm.addEventListener('submit', (e) => {
        e.preventDefault();
        this.handleEditReel();
      });
    }

    // Video upload
    this.setupVideoUpload();

    // Keyboard navigation for reel player
    document.addEventListener('keydown', (e) => {
      const modal = document.getElementById('reelPlayerModal');
      if (modal && modal.classList.contains('active')) {
        if (e.key === 'ArrowUp') this.previousReel();
        if (e.key === 'ArrowDown') this.nextReel();
        if (e.key === ' ') this.togglePlayPause();
        if (e.key === 'Escape') Modals.close('reelPlayerModal');
      }
    });
  },

  /**
   * Setup video upload
   */
  setupVideoUpload() {
    const uploadArea = document.getElementById('reelVideoUploadArea');
    const fileInput = document.getElementById('reelVideoInput');
    const preview = document.getElementById('reelVideoPreview');
    const previewVideo = document.getElementById('reelPreviewVideo');
    const removeBtn = document.getElementById('removeReelVideoBtn');

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
        this.handleVideoSelect(files[0]);
      }
    });

    // File input change
    fileInput.addEventListener('change', (e) => {
      if (e.target.files.length > 0) {
        this.handleVideoSelect(e.target.files[0]);
      }
    });

    // Remove video
    if (removeBtn) {
      removeBtn.addEventListener('click', () => {
        fileInput.value = '';
        preview.style.display = 'none';
        uploadArea.style.display = 'flex';
        if (previewVideo) previewVideo.src = '';
      });
    }
  },

  /**
   * Handle video selection
   */
  handleVideoSelect(file) {
    if (!file.type.startsWith('video/')) {
      Utils.showToast('Please select a video file', 'error');
      return;
    }

    // Check duration (max 60 seconds)
    const video = document.createElement('video');
    video.preload = 'metadata';

    video.onloadedmetadata = () => {
      window.URL.revokeObjectURL(video.src);

      if (video.duration > 60) {
        Utils.showToast('Video must be 60 seconds or less', 'error');
        return;
      }

      const reader = new FileReader();
      reader.onload = (e) => {
        const preview = document.getElementById('reelVideoPreview');
        const previewVideo = document.getElementById('reelPreviewVideo');
        const uploadArea = document.getElementById('reelVideoUploadArea');

        previewVideo.src = e.target.result;
        preview.style.display = 'block';
        uploadArea.style.display = 'none';
      };
      reader.readAsDataURL(file);
    };

    video.src = URL.createObjectURL(file);
  },

  /**
   * Load reels
   */
  async loadReels() {
    const container = document.getElementById('reelsContainer');
    if (!container) return;

    container.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i><p>Loading reels...</p></div>';

    try {
      const params = {
        page: this.currentPage,
        page_size: this.perPage
      };

      if (this.filters.search) params.search = this.filters.search;
      if (this.filters.user !== 'all') params.user = this.filters.user;

      // Apply sort
      if (this.filters.sortBy === 'views') {
        params.ordering = '-views_count';
      } else if (this.filters.sortBy === 'likes') {
        params.ordering = '-likes_count';
      } else if (this.filters.sortBy === 'comments') {
        params.ordering = '-comments_count';
      } else {
        params.ordering = '-created_at';
      }

      const response = await API.get('/reels/', params);
      this.reels = response.results || response;

      this.renderReels(this.reels);
      this.renderPagination(response);
    } catch (error) {
      console.error('Error loading reels:', error);
      container.innerHTML = '<p style="text-align: center; padding: 2rem;">Error loading reels</p>';
      Utils.showToast('Failed to load reels', 'error');
    }
  },

  /**
   * Render reels grid
   */
  renderReels(reels) {
    const container = document.getElementById('reelsContainer');
    if (!container) return;

    if (reels.length === 0) {
      container.innerHTML = '<p style="text-align: center; padding: 2rem;">No reels found</p>';
      return;
    }

    container.innerHTML = reels.map((reel, index) => `
            <div class="reel-card" data-reel-id="${reel.id}">
                <div class="reel-thumbnail" onclick="ReelsManager.playReel(${index})">
                    <video 
                        src="${reel.video_url}" 
                        poster="${reel.thumbnail_url || ''}"
                        muted
                        loop
                        class="reel-preview-video"
                        onmouseenter="this.play()"
                        onmouseleave="this.pause(); this.currentTime = 0;"
                    ></video>
                    <div class="reel-play-icon">
                        <i class="fas fa-play"></i>
                    </div>
                    <div class="reel-duration-badge">
                        ${this.formatDuration(reel.duration || 0)}
                    </div>
                    <div class="reel-overlay">
                        <div class="reel-user-info">
                            <img src="${reel.user?.profile_picture || `https://ui-avatars.com/api/?name=${encodeURIComponent(reel.user?.username || 'User')}`}" 
                                 alt="${reel.user?.username}">
                            <span>${reel.user?.username || 'Unknown'}</span>
                        </div>
                        <div class="reel-stats">
                            <span><i class="fas fa-eye"></i> ${this.formatCount(reel.views_count || 0)}</span>
                            <span><i class="fas fa-heart"></i> ${this.formatCount(reel.likes_count || 0)}</span>
                            <span><i class="fas fa-comment"></i> ${this.formatCount(reel.comments_count || 0)}</span>
                        </div>
                    </div>
                </div>
                <div class="reel-info">
                    <p class="reel-caption">${Utils.truncateText(reel.caption || '', 60)}</p>
                    <div class="reel-actions">
                        <button class="btn-icon" onclick="ReelsManager.playReel(${index})" title="Play">
                            <i class="fas fa-play"></i>
                        </button>
                        <button class="btn-icon" onclick="ReelsManager.editReel(${reel.id})" title="Edit">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn-icon" onclick="ReelsManager.downloadReel(${reel.id})" title="Download">
                            <i class="fas fa-download"></i>
                        </button>
                        <button class="btn-icon btn-danger" onclick="ReelsManager.deleteReel(${reel.id})" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
  },

  /**
   * Format duration (seconds to MM:SS)
   */
  formatDuration(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  },

  /**
   * Format count (1000 -> 1K)
   */
  formatCount(count) {
    if (count >= 1000000) return (count / 1000000).toFixed(1) + 'M';
    if (count >= 1000) return (count / 1000).toFixed(1) + 'K';
    return count.toString();
  },

  /**
   * Play reel in full-screen player
   */
  async playReel(index) {
    this.currentReelIndex = index;
    const reel = this.reels[index];

    Modals.open('reelPlayerModal');
    const player = document.getElementById('reelPlayerContent');

    player.innerHTML = `
            <div class="reel-player-video-container">
                <video 
                    id="reelPlayerVideo"
                    src="${reel.video_url}" 
                    autoplay
                    loop
                    class="reel-player-video"
                ></video>
                
                <div class="reel-player-controls">
                    <button class="reel-control-btn" id="playPauseBtn" onclick="ReelsManager.togglePlayPause()">
                        <i class="fas fa-pause"></i>
                    </button>
                    <div class="reel-progress-bar" id="reelProgressBar">
                        <div class="reel-progress-fill" id="reelProgressFill"></div>
                    </div>
                    <button class="reel-control-btn" id="muteBtn" onclick="ReelsManager.toggleMute()">
                        <i class="fas fa-volume-up"></i>
                    </button>
                </div>

                <button class="reel-player-close" onclick="Modals.close('reelPlayerModal')">
                    <i class="fas fa-times"></i>
                </button>
            </div>

            <div class="reel-player-sidebar">
                <div class="reel-player-user">
                    <img src="${reel.user?.profile_picture || `https://ui-avatars.com/api/?name=${encodeURIComponent(reel.user?.username || 'User')}`}" 
                         alt="${reel.user?.username}">
                    <div>
                        <h4>${reel.user?.username || 'Unknown'}</h4>
                        <p>${Utils.formatDate(reel.created_at)}</p>
                    </div>
                </div>

                <div class="reel-player-caption">
                    <p>${reel.caption || 'No caption'}</p>
                    ${reel.audio_name ? `<p class="reel-audio"><i class="fas fa-music"></i> ${reel.audio_name}</p>` : ''}
                </div>

                <div class="reel-player-stats">
                    <div class="stat-item">
                        <i class="fas fa-eye"></i>
                        <span>${this.formatCount(reel.views_count || 0)} views</span>
                    </div>
                    <div class="stat-item">
                        <i class="fas fa-heart"></i>
                        <span>${this.formatCount(reel.likes_count || 0)} likes</span>
                    </div>
                    <div class="stat-item">
                        <i class="fas fa-comment"></i>
                        <span>${this.formatCount(reel.comments_count || 0)} comments</span>
                    </div>
                </div>

                <div class="reel-player-actions">
                    <button class="btn-secondary btn-sm" onclick="ReelsManager.viewComments(${reel.id})">
                        <i class="fas fa-comment"></i> Comments
                    </button>
                    <button class="btn-secondary btn-sm" onclick="ReelsManager.viewLikes(${reel.id})">
                        <i class="fas fa-heart"></i> Likes
                    </button>
                    <button class="btn-secondary btn-sm" onclick="ReelsManager.downloadReel(${reel.id})">
                        <i class="fas fa-download"></i> Download
                    </button>
                </div>

                <div class="reel-player-nav">
                    <button class="reel-nav-btn" onclick="ReelsManager.previousReel()" ${index === 0 ? 'disabled' : ''}>
                        <i class="fas fa-chevron-up"></i> Previous
                    </button>
                    <button class="reel-nav-btn" onclick="ReelsManager.nextReel()" ${index === this.reels.length - 1 ? 'disabled' : ''}>
                        <i class="fas fa-chevron-down"></i> Next
                    </button>
                </div>
            </div>
        `;

    // Setup video progress
    this.setupVideoProgress();

    // Mark as viewed
    try {
      await API.post(`/reels/${reel.id}/view/`, {});
    } catch (error) {
      console.error('Error marking reel as viewed:', error);
    }
  },

  /**
   * Setup video progress tracking
   */
  setupVideoProgress() {
    const video = document.getElementById('reelPlayerVideo');
    const progressFill = document.getElementById('reelProgressFill');

    if (!video || !progressFill) return;

    video.addEventListener('timeupdate', () => {
      const progress = (video.currentTime / video.duration) * 100;
      progressFill.style.width = `${progress}%`;
    });

    // Click to seek
    const progressBar = document.getElementById('reelProgressBar');
    if (progressBar) {
      progressBar.addEventListener('click', (e) => {
        const rect = progressBar.getBoundingClientRect();
        const pos = (e.clientX - rect.left) / rect.width;
        video.currentTime = pos * video.duration;
      });
    }
  },

  /**
   * Toggle play/pause
   */
  togglePlayPause() {
    const video = document.getElementById('reelPlayerVideo');
    const btn = document.getElementById('playPauseBtn');

    if (!video || !btn) return;

    if (video.paused) {
      video.play();
      btn.innerHTML = '<i class="fas fa-pause"></i>';
    } else {
      video.pause();
      btn.innerHTML = '<i class="fas fa-play"></i>';
    }
  },

  /**
   * Toggle mute
   */
  toggleMute() {
    const video = document.getElementById('reelPlayerVideo');
    const btn = document.getElementById('muteBtn');

    if (!video || !btn) return;

    video.muted = !video.muted;
    btn.innerHTML = video.muted ? '<i class="fas fa-volume-mute"></i>' : '<i class="fas fa-volume-up"></i>';
  },

  /**
   * Previous reel
   */
  previousReel() {
    if (this.currentReelIndex > 0) {
      this.playReel(this.currentReelIndex - 1);
    }
  },

  /**
   * Next reel
   */
  nextReel() {
    if (this.currentReelIndex < this.reels.length - 1) {
      this.playReel(this.currentReelIndex + 1);
    }
  },

  /**
   * View comments
   */
  async viewComments(id) {
    Modals.open('reelCommentsModal');
    const body = document.getElementById('reelCommentsBody');
    body.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i></div>';

    try {
      const comments = await API.get(`/reels/${id}/comments/`);

      if (comments.length === 0) {
        body.innerHTML = '<p style="text-align: center; padding: 2rem;">No comments yet</p>';
        return;
      }

      body.innerHTML = `
                <div class="comments-list">
                    ${comments.map(comment => `
                        <div class="comment-item">
                            <img src="${comment.user?.profile_picture || `https://ui-avatars.com/api/?name=${encodeURIComponent(comment.user?.username || 'User')}`}" 
                                 alt="${comment.user?.username}">
                            <div class="comment-content">
                                <h4>${comment.user?.username || 'Unknown'}</h4>
                                <p>${comment.text}</p>
                                <span>${Utils.formatDate(comment.created_at)}</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
    } catch (error) {
      console.error('Error loading comments:', error);
      body.innerHTML = '<p style="text-align: center; color: #ef4444;">Error loading comments</p>';
    }
  },

  /**
   * View likes
   */
  async viewLikes(id) {
    Modals.open('reelLikesModal');
    const body = document.getElementById('reelLikesBody');
    body.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i></div>';

    try {
      const likes = await API.get(`/reels/${id}/likes/`);

      if (likes.length === 0) {
        body.innerHTML = '<p style="text-align: center; padding: 2rem;">No likes yet</p>';
        return;
      }

      body.innerHTML = `
                <div class="likes-list">
                    ${likes.map(like => `
                        <div class="like-item">
                            <img src="${like.user?.profile_picture || `https://ui-avatars.com/api/?name=${encodeURIComponent(like.user?.username || 'User')}`}" 
                                 alt="${like.user?.username}">
                            <div>
                                <h4>${like.user?.username || 'Unknown'}</h4>
                                <p>${Utils.formatDate(like.created_at)}</p>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
    } catch (error) {
      console.error('Error loading likes:', error);
      body.innerHTML = '<p style="text-align: center; color: #ef4444;">Error loading likes</p>';
    }
  },

  /**
   * Edit reel
   */
  async editReel(id) {
    try {
      const reel = await API.get(`/reels/${id}/`);

      document.getElementById('editReelId').value = reel.id;
      document.getElementById('editReelCaption').value = reel.caption || '';
      document.getElementById('editReelAudio').value = reel.audio_name || '';

      Modals.close('reelPlayerModal');
      Modals.open('editReelModal');
    } catch (error) {
      console.error('Error loading reel:', error);
      Utils.showToast('Failed to load reel', 'error');
    }
  },

  /**
   * Handle add reel
   */
  async handleAddReel() {
    const fileInput = document.getElementById('reelVideoInput');
    const caption = document.getElementById('addReelCaption').value;
    const audioName = document.getElementById('addReelAudio').value;
    const userId = document.getElementById('addReelUser').value;

    if (!fileInput.files[0]) {
      Utils.showToast('Please select a video', 'error');
      return;
    }

    if (!userId) {
      Utils.showToast('Please select a user', 'error');
      return;
    }

    const formData = new FormData();
    formData.append('video', fileInput.files[0]);
    formData.append('caption', caption);
    formData.append('audio_name', audioName);
    formData.append('user', userId);

    try {
      await API.post('/reels/', formData);
      Utils.showToast('Reel created successfully', 'success');
      Modals.close('addReelModal');
      document.getElementById('addReelForm').reset();
      document.getElementById('reelVideoPreview').style.display = 'none';
      document.getElementById('reelVideoUploadArea').style.display = 'flex';
      this.loadReels();
    } catch (error) {
      console.error('Error creating reel:', error);
      Utils.showToast('Failed to create reel', 'error');
    }
  },

  /**
   * Handle edit reel
   */
  async handleEditReel() {
    const id = document.getElementById('editReelId').value;
    const formData = {
      caption: document.getElementById('editReelCaption').value,
      audio_name: document.getElementById('editReelAudio').value
    };

    try {
      await API.put(`/reels/${id}/`, formData);
      Utils.showToast('Reel updated successfully', 'success');
      Modals.close('editReelModal');
      this.loadReels();
    } catch (error) {
      console.error('Error updating reel:', error);
      Utils.showToast('Failed to update reel', 'error');
    }
  },

  /**
   * Delete reel
   */
  async deleteReel(id) {
    if (!confirm('Are you sure you want to delete this reel?')) return;

    try {
      await API.delete(`/reels/${id}/`);
      Utils.showToast('Reel deleted successfully', 'success');
      Modals.close('reelPlayerModal');
      this.loadReels();
    } catch (error) {
      console.error('Error deleting reel:', error);
      Utils.showToast('Failed to delete reel', 'error');
    }
  },

  /**
   * Download reel
   */
  async downloadReel(id) {
    try {
      const reel = await API.get(`/reels/${id}/`);
      const link = document.createElement('a');
      link.href = reel.video_url;
      link.download = `reel-${id}.mp4`;
      link.click();
      Utils.showToast('Download started', 'success');
    } catch (error) {
      console.error('Error downloading reel:', error);
      Utils.showToast('Failed to download reel', 'error');
    }
  },

  /**
   * Render pagination
   */
  renderPagination(response) {
    const pagination = document.getElementById('reelsPagination');
    if (!pagination || !response.count) return;

    const totalPages = Math.ceil(response.count / this.perPage);
    if (totalPages <= 1) {
      pagination.innerHTML = '';
      return;
    }

    let html = '<div class="pagination">';

    html += `<button class="pagination-btn" ${this.currentPage === 1 ? 'disabled' : ''} 
                 onclick="ReelsManager.goToPage(${this.currentPage - 1})">
                 <i class="fas fa-chevron-left"></i>
                 </button>`;

    for (let i = 1; i <= Math.min(totalPages, 5); i++) {
      html += `<button class="pagination-btn ${i === this.currentPage ? 'active' : ''}" 
                     onclick="ReelsManager.goToPage(${i})">${i}</button>`;
    }

    html += `<button class="pagination-btn" ${this.currentPage === totalPages ? 'disabled' : ''} 
                 onclick="ReelsManager.goToPage(${this.currentPage + 1})">
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
    this.loadReels();
  }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ReelsManager;
}
