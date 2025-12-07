/**
 * Live Streams Management
 * Real-time monitoring and management of live streams
 */

const LiveStreamsManager = {
  currentPage: 1,
  perPage: 20,
  filters: {
    search: '',
    status: 'all',
    streamer: 'all'
  },
  updateInterval: null,

  /**
   * Initialize live streams management
   */
  init() {
    this.setupEventListeners();
    this.loadStreams();
    this.startRealTimeUpdates();
  },

  /**
   * Setup event listeners
   */
  setupEventListeners() {
    // Search
    const searchInput = document.getElementById('streamSearch');
    if (searchInput) {
      searchInput.addEventListener('input', Utils.debounce((e) => {
        this.filters.search = e.target.value;
        this.currentPage = 1;
        this.loadStreams();
      }, 300));
    }

    // Filters
    ['streamStatusFilter', 'streamStreamerFilter'].forEach(id => {
      const filter = document.getElementById(id);
      if (filter) {
        filter.addEventListener('change', (e) => {
          const filterName = id.replace('stream', '').replace('Filter', '').toLowerCase();
          this.filters[filterName] = e.target.value;
          this.currentPage = 1;
          this.loadStreams();
        });
      }
    });
  },

  /**
   * Start real-time updates
   */
  startRealTimeUpdates() {
    // Update every 5 seconds
    this.updateInterval = setInterval(() => {
      this.loadStreams(true); // Silent update
      this.updateLiveMonitoring();
    }, 5000);
  },

  /**
   * Stop real-time updates
   */
  stopRealTimeUpdates() {
    if (this.updateInterval) {
      clearInterval(this.updateInterval);
      this.updateInterval = null;
    }
  },

  /**
   * Load streams
   */
  async loadStreams(silent = false) {
    const container = document.getElementById('streamsContainer');
    if (!container) return;

    if (!silent) {
      container.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i><p>Loading streams...</p></div>';
    }

    try {
      const params = {
        page: this.currentPage,
        page_size: this.perPage
      };

      if (this.filters.search) params.search = this.filters.search;
      if (this.filters.status !== 'all') params.status = this.filters.status;
      if (this.filters.streamer !== 'all') params.streamer = this.filters.streamer;

      const response = await API.get('/live/streams/', params);
      const streams = response.results || response;

      this.renderStreams(streams);
      if (!silent) {
        this.renderPagination(response);
      }
    } catch (error) {
      console.error('Error loading streams:', error);
      if (!silent) {
        container.innerHTML = '<p style="text-align: center; padding: 2rem;">Error loading streams</p>';
        Utils.showToast('Failed to load streams', 'error');
      }
    }
  },

  /**
   * Render streams
   */
  renderStreams(streams) {
    const container = document.getElementById('streamsContainer');
    if (!container) return;

    if (streams.length === 0) {
      container.innerHTML = '<p style="text-align: center; padding: 2rem;">No streams found</p>';
      return;
    }

    container.innerHTML = streams.map(stream => {
      const isLive = stream.status === 'live';
      const duration = this.calculateDuration(stream.started_at, stream.ended_at);

      return `
                <div class="stream-card ${stream.status}" data-stream-id="${stream.id}">
                    <div class="stream-thumbnail" onclick="LiveStreamsManager.viewStream(${stream.id})">
                        <img src="${stream.thumbnail_url || 'https://via.placeholder.com/400x225'}" alt="Stream">
                        ${isLive ? '<div class="live-indicator"><span class="pulse-dot"></span> LIVE</div>' : ''}
                        <div class="stream-status-badge ${stream.status}">
                            ${this.getStatusLabel(stream.status)}
                        </div>
                        ${isLive ? `<div class="viewer-count"><i class="fas fa-eye"></i> ${this.formatCount(stream.current_viewers || 0)}</div>` : ''}
                    </div>
                    <div class="stream-info">
                        <div class="stream-header">
                            <img src="${stream.streamer?.profile_picture || `https://ui-avatars.com/api/?name=${encodeURIComponent(stream.streamer?.username || 'User')}`}" 
                                 alt="${stream.streamer?.username}"
                                 class="stream-avatar">
                            <div class="stream-meta">
                                <h4>${stream.title || 'Untitled Stream'}</h4>
                                <p class="stream-streamer">${stream.streamer?.username || 'Unknown'}</p>
                            </div>
                        </div>
                        <p class="stream-description">${Utils.truncateText(stream.description || '', 80)}</p>
                        <div class="stream-stats">
                            <span><i class="fas fa-eye"></i> ${this.formatCount(stream.peak_viewers || 0)} peak</span>
                            <span><i class="fas fa-clock"></i> ${duration}</span>
                            <span><i class="fas fa-comment"></i> ${this.formatCount(stream.comments_count || 0)}</span>
                        </div>
                        <div class="stream-actions">
                            <button class="btn-icon" onclick="LiveStreamsManager.viewStream(${stream.id})" title="View">
                                <i class="fas fa-eye"></i>
                            </button>
                            ${isLive ?
          `<button class="btn-icon btn-danger" onclick="LiveStreamsManager.endStream(${stream.id})" title="End Stream">
                                    <i class="fas fa-stop"></i>
                                </button>` :
          `<button class="btn-icon btn-danger" onclick="LiveStreamsManager.deleteStream(${stream.id})" title="Delete">
                                    <i class="fas fa-trash"></i>
                                </button>`
        }
                            <button class="btn-icon" onclick="LiveStreamsManager.viewViewers(${stream.id})" title="Viewers">
                                <i class="fas fa-users"></i>
                            </button>
                            <button class="btn-icon" onclick="LiveStreamsManager.exportAnalytics(${stream.id})" title="Export">
                                <i class="fas fa-download"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `;
    }).join('');
  },

  /**
   * Get status label
   */
  getStatusLabel(status) {
    const labels = {
      waiting: 'Waiting',
      live: 'Live',
      ended: 'Ended'
    };
    return labels[status] || status;
  },

  /**
   * Calculate duration
   */
  calculateDuration(startedAt, endedAt) {
    if (!startedAt) return 'Not started';

    const start = new Date(startedAt);
    const end = endedAt ? new Date(endedAt) : new Date();
    const diff = end - start;

    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  },

  /**
   * Format count
   */
  formatCount(count) {
    if (count >= 1000000) return (count / 1000000).toFixed(1) + 'M';
    if (count >= 1000) return (count / 1000).toFixed(1) + 'K';
    return count.toString();
  },

  /**
   * View stream details
   */
  async viewStream(id) {
    Modals.open('streamDetailsModal');
    const body = document.getElementById('streamDetailsBody');
    body.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i></div>';

    try {
      const stream = await API.get(`/live/streams/${id}/`);
      const isLive = stream.status === 'live';

      body.innerHTML = `
                <div class="stream-details-grid">
                    <div class="stream-details-preview">
                        ${isLive ?
          `<div class="stream-preview-container">
                                <iframe src="${stream.stream_url}" frameborder="0" allowfullscreen></iframe>
                                <div class="live-indicator-large">
                                    <span class="pulse-dot"></span> LIVE
                                </div>
                            </div>` :
          `<img src="${stream.thumbnail_url || 'https://via.placeholder.com/800x450'}" alt="Stream">`
        }
                    </div>
                    <div class="stream-details-content">
                        <div class="stream-details-header">
                            <img src="${stream.streamer?.profile_picture || `https://ui-avatars.com/api/?name=${encodeURIComponent(stream.streamer?.username || 'User')}`}" 
                                 alt="${stream.streamer?.username}">
                            <div>
                                <h3>${stream.title || 'Untitled Stream'}</h3>
                                <p>${stream.streamer?.username || 'Unknown'}</p>
                                <span class="stream-status-badge ${stream.status}">${this.getStatusLabel(stream.status)}</span>
                            </div>
                        </div>

                        <div class="stream-details-description">
                            <p>${stream.description || 'No description'}</p>
                        </div>

                        <div class="stream-details-stats">
                            <div class="stat-box">
                                <i class="fas fa-eye"></i>
                                <div>
                                    <h4>${this.formatCount(stream.current_viewers || 0)}</h4>
                                    <p>Current Viewers</p>
                                </div>
                            </div>
                            <div class="stat-box">
                                <i class="fas fa-chart-line"></i>
                                <div>
                                    <h4>${this.formatCount(stream.peak_viewers || 0)}</h4>
                                    <p>Peak Viewers</p>
                                </div>
                            </div>
                            <div class="stat-box">
                                <i class="fas fa-clock"></i>
                                <div>
                                    <h4>${this.calculateDuration(stream.started_at, stream.ended_at)}</h4>
                                    <p>Duration</p>
                                </div>
                            </div>
                            <div class="stat-box">
                                <i class="fas fa-comment"></i>
                                <div>
                                    <h4>${this.formatCount(stream.comments_count || 0)}</h4>
                                    <p>Comments</p>
                                </div>
                            </div>
                            <div class="stat-box">
                                <i class="fas fa-heart"></i>
                                <div>
                                    <h4>${this.formatCount(stream.reactions_count || 0)}</h4>
                                    <p>Reactions</p>
                                </div>
                            </div>
                        </div>

                        <div class="stream-details-actions">
                            ${isLive ?
          `<button class="btn-danger" onclick="LiveStreamsManager.endStream(${stream.id})">
                                    <i class="fas fa-stop"></i> End Stream
                                </button>` :
          `<button class="btn-danger" onclick="LiveStreamsManager.deleteStream(${stream.id})">
                                    <i class="fas fa-trash"></i> Delete Stream
                                </button>`
        }
                            <button class="btn-secondary" onclick="LiveStreamsManager.viewViewers(${stream.id})">
                                <i class="fas fa-users"></i> View Viewers
                            </button>
                            <button class="btn-secondary" onclick="LiveStreamsManager.viewComments(${stream.id})">
                                <i class="fas fa-comment"></i> View Comments
                            </button>
                            <button class="btn-secondary" onclick="LiveStreamsManager.exportAnalytics(${stream.id})">
                                <i class="fas fa-download"></i> Export Analytics
                            </button>
                        </div>
                    </div>
                </div>
            `;

      // Start real-time updates for live streams
      if (isLive) {
        this.startStreamUpdates(id);
      }
    } catch (error) {
      console.error('Error loading stream:', error);
      body.innerHTML = '<p style="text-align: center; color: #ef4444;">Error loading stream details</p>';
    }
  },

  /**
   * Start stream updates
   */
  startStreamUpdates(streamId) {
    // Update stream stats every 3 seconds
    const updateInterval = setInterval(async () => {
      try {
        const stream = await API.get(`/live/streams/${streamId}/`);

        // Update viewer count
        const viewerCountEl = document.querySelector('.stream-details-stats .stat-box:nth-child(1) h4');
        if (viewerCountEl) {
          viewerCountEl.textContent = this.formatCount(stream.current_viewers || 0);
        }

        // If stream ended, stop updates
        if (stream.status !== 'live') {
          clearInterval(updateInterval);
          this.viewStream(streamId); // Reload
        }
      } catch (error) {
        clearInterval(updateInterval);
      }
    }, 3000);

    // Clear interval when modal closes
    const modal = document.getElementById('streamDetailsModal');
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (!modal.classList.contains('active')) {
          clearInterval(updateInterval);
          observer.disconnect();
        }
      });
    });
    observer.observe(modal, { attributes: true, attributeFilter: ['class'] });
  },

  /**
   * View viewers
   */
  async viewViewers(id) {
    Modals.open('streamViewersModal');
    const body = document.getElementById('streamViewersBody');
    body.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i></div>';

    try {
      const viewers = await API.get(`/live/streams/${id}/viewers/`);

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
                                <p>Joined ${Utils.formatDate(viewer.joined_at)}</p>
                            </div>
                            ${viewer.is_active ? '<span class="online-badge">Online</span>' : ''}
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
   * View comments
   */
  async viewComments(id) {
    Modals.open('streamCommentsModal');
    const body = document.getElementById('streamCommentsBody');
    body.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i></div>';

    try {
      const comments = await API.get(`/live/streams/${id}/comments/`);

      if (comments.length === 0) {
        body.innerHTML = '<p style="text-align: center; padding: 2rem;">No comments yet</p>';
        return;
      }

      body.innerHTML = `
                <div class="comments-feed">
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
   * Update live monitoring dashboard
   */
  async updateLiveMonitoring() {
    try {
      const stats = await API.get('/live/streams/stats/');

      // Update live count
      const liveCountEl = document.getElementById('liveStreamsCount');
      if (liveCountEl) {
        liveCountEl.textContent = stats.live_count || 0;
      }

      // Update total viewers
      const totalViewersEl = document.getElementById('totalViewers');
      if (totalViewersEl) {
        totalViewersEl.textContent = this.formatCount(stats.total_viewers || 0);
      }
    } catch (error) {
      console.error('Error updating monitoring:', error);
    }
  },

  /**
   * End stream
   */
  async endStream(id) {
    if (!confirm('Are you sure you want to end this stream?')) return;

    try {
      await API.post(`/live/streams/${id}/end/`, {});
      Utils.showToast('Stream ended successfully', 'success');
      Modals.close('streamDetailsModal');
      this.loadStreams();
    } catch (error) {
      console.error('Error ending stream:', error);
      Utils.showToast('Failed to end stream', 'error');
    }
  },

  /**
   * Delete stream
   */
  async deleteStream(id) {
    if (!confirm('Are you sure you want to delete this stream?')) return;

    try {
      await API.delete(`/live/streams/${id}/`);
      Utils.showToast('Stream deleted successfully', 'success');
      Modals.close('streamDetailsModal');
      this.loadStreams();
    } catch (error) {
      console.error('Error deleting stream:', error);
      Utils.showToast('Failed to delete stream', 'error');
    }
  },

  /**
   * Export analytics
   */
  exportAnalytics(id) {
    Utils.showToast('Export feature coming soon', 'info');
  },

  /**
   * Render pagination
   */
  renderPagination(response) {
    const pagination = document.getElementById('streamsPagination');
    if (!pagination || !response.count) return;

    const totalPages = Math.ceil(response.count / this.perPage);
    if (totalPages <= 1) {
      pagination.innerHTML = '';
      return;
    }

    let html = '<div class="pagination">';

    html += `<button class="pagination-btn" ${this.currentPage === 1 ? 'disabled' : ''} 
                 onclick="LiveStreamsManager.goToPage(${this.currentPage - 1})">
                 <i class="fas fa-chevron-left"></i>
                 </button>`;

    for (let i = 1; i <= Math.min(totalPages, 5); i++) {
      html += `<button class="pagination-btn ${i === this.currentPage ? 'active' : ''}" 
                     onclick="LiveStreamsManager.goToPage(${i})">${i}</button>`;
    }

    html += `<button class="pagination-btn" ${this.currentPage === totalPages ? 'disabled' : ''} 
                 onclick="LiveStreamsManager.goToPage(${this.currentPage + 1})">
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
    this.loadStreams();
  },

  /**
   * Cleanup
   */
  destroy() {
    this.stopRealTimeUpdates();
  }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
  module.exports = LiveStreamsManager;
}
