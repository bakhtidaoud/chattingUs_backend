/**
 * Posts Management
 * Comprehensive post management with grid/list views, moderation, and bulk actions
 */

const PostsManager = {
  currentPage: 1,
  perPage: 20,
  currentView: 'grid', // 'grid' or 'list'
  sortBy: 'created_at',
  sortOrder: 'desc',
  filters: {
    search: '',
    status: 'all',
    sort: 'recent'
  },
  selectedPosts: new Set(),

  /**
   * Initialize posts management
   */
  init() {
    this.setupEventListeners();
    this.loadPosts();
  },

  /**
   * Setup event listeners
   */
  setupEventListeners() {
    // View toggle
    document.querySelectorAll('.view-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const view = btn.dataset.view;
        this.switchView(view);
      });
    });

    // Search
    const searchInput = document.getElementById('postSearch');
    if (searchInput) {
      searchInput.addEventListener('input', Utils.debounce((e) => {
        this.filters.search = e.target.value;
        this.currentPage = 1;
        this.loadPosts();
      }, 300));
    }

    // Filters
    ['postStatusFilter', 'postSortFilter'].forEach(id => {
      const filter = document.getElementById(id);
      if (filter) {
        filter.addEventListener('change', (e) => {
          const filterName = id.replace('post', '').replace('Filter', '').toLowerCase();
          this.filters[filterName] = e.target.value;
          this.currentPage = 1;
          this.loadPosts();
        });
      }
    });

    // Add post button
    const addPostBtn = document.getElementById('addPostBtn');
    if (addPostBtn) {
      addPostBtn.addEventListener('click', () => {
        Modals.open('addPostModal');
      });
    }

    // Add post form
    const addPostForm = document.getElementById('addPostForm');
    if (addPostForm) {
      addPostForm.addEventListener('submit', (e) => {
        e.preventDefault();
        this.handleAddPost();
      });
    }

    // Edit post form
    const editPostForm = document.getElementById('editPostForm');
    if (editPostForm) {
      editPostForm.addEventListener('submit', (e) => {
        e.preventDefault();
        this.handleEditPost();
      });
    }

    // Image upload
    this.setupImageUpload();

    // Select all checkbox
    const selectAll = document.getElementById('selectAllPosts');
    if (selectAll) {
      selectAll.addEventListener('change', (e) => {
        this.toggleSelectAll(e.target.checked);
      });
    }

    // Bulk actions
    const bulkArchiveBtn = document.getElementById('bulkArchiveBtn');
    if (bulkArchiveBtn) {
      bulkArchiveBtn.addEventListener('click', () => this.handleBulkArchive());
    }

    const bulkDeleteBtn = document.getElementById('bulkDeletePostsBtn');
    if (bulkDeleteBtn) {
      bulkDeleteBtn.addEventListener('click', () => this.handleBulkDelete());
    }

    const clearSelectionBtn = document.getElementById('clearPostSelectionBtn');
    if (clearSelectionBtn) {
      clearSelectionBtn.addEventListener('click', () => this.clearSelection());
    }

    // Export button
    const exportBtn = document.getElementById('exportPostsBtn');
    if (exportBtn) {
      exportBtn.addEventListener('click', () => this.exportPosts());
    }
  },

  /**
   * Setup image upload
   */
  setupImageUpload() {
    const uploadArea = document.getElementById('imageUploadArea');
    const fileInput = document.getElementById('postImageInput');
    const preview = document.getElementById('imagePreview');
    const previewImg = document.getElementById('previewImg');
    const removeBtn = document.getElementById('removeImageBtn');

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
        this.handleImageSelect(files[0]);
      }
    });

    // File input change
    fileInput.addEventListener('change', (e) => {
      if (e.target.files.length > 0) {
        this.handleImageSelect(e.target.files[0]);
      }
    });

    // Remove image
    if (removeBtn) {
      removeBtn.addEventListener('click', () => {
        fileInput.value = '';
        preview.style.display = 'none';
        uploadArea.style.display = 'flex';
      });
    }
  },

  /**
   * Handle image selection
   */
  handleImageSelect(file) {
    if (!file.type.startsWith('image/')) {
      Utils.showToast('Please select an image file', 'error');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const preview = document.getElementById('imagePreview');
      const previewImg = document.getElementById('previewImg');
      const uploadArea = document.getElementById('imageUploadArea');

      previewImg.src = e.target.result;
      preview.style.display = 'block';
      uploadArea.style.display = 'none';
    };
    reader.readAsDataURL(file);
  },

  /**
   * Switch view
   */
  switchView(view) {
    this.currentView = view;

    // Update buttons
    document.querySelectorAll('.view-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.view === view);
    });

    // Toggle views
    const gridView = document.getElementById('postsGrid');
    const listView = document.getElementById('postsListView');

    if (view === 'grid') {
      if (gridView) gridView.style.display = 'grid';
      if (listView) listView.style.display = 'none';
    } else {
      if (gridView) gridView.style.display = 'none';
      if (listView) listView.style.display = 'block';
    }

    this.loadPosts();
  },

  /**
   * Load posts
   */
  async loadPosts() {
    const gridView = document.getElementById('postsGrid');
    const tableBody = document.getElementById('postsTableBody');

    if (this.currentView === 'grid' && gridView) {
      gridView.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i><p>Loading posts...</p></div>';
    } else if (tableBody) {
      tableBody.innerHTML = '<tr><td colspan="8" class="loading-cell"><i class="fas fa-spinner fa-spin"></i> Loading posts...</td></tr>';
    }

    try {
      const params = {
        page: this.currentPage,
        page_size: this.perPage,
        ordering: this.sortOrder === 'desc' ? `-${this.sortBy}` : this.sortBy
      };

      if (this.filters.search) params.search = this.filters.search;
      if (this.filters.status !== 'all') params.is_archived = this.filters.status === 'archived';

      // Apply sort filter
      if (this.filters.sort === 'likes') {
        params.ordering = '-likes_count';
      } else if (this.filters.sort === 'comments') {
        params.ordering = '-comments_count';
      }

      const response = await API.getPosts(params);
      const posts = response.results || response;

      if (this.currentView === 'grid') {
        this.renderPostsGrid(posts);
      } else {
        this.renderPostsList(posts);
      }

      this.renderPagination(response);
    } catch (error) {
      console.error('Error loading posts:', error);
      Utils.showToast('Failed to load posts', 'error');
    }
  },

  /**
   * Render posts grid
   */
  renderPostsGrid(posts) {
    const gridView = document.getElementById('postsGrid');
    if (!gridView) return;

    if (posts.length === 0) {
      gridView.innerHTML = '<p style="text-align: center; padding: 2rem; grid-column: 1/-1;">No posts found</p>';
      return;
    }

    gridView.innerHTML = posts.map(post => `
            <div class="post-card" data-post-id="${post.id}">
                <div class="post-card-checkbox">
                    <input type="checkbox" class="post-checkbox" data-post-id="${post.id}" 
                           ${this.selectedPosts.has(post.id) ? 'checked' : ''}>
                </div>
                <div class="post-card-image" onclick="PostsManager.viewPost(${post.id})">
                    <img src="${post.image || 'https://via.placeholder.com/400'}" alt="Post" loading="lazy">
                    <div class="post-card-overlay">
                        <div class="post-stats">
                            <span><i class="fas fa-heart"></i> ${post.likes_count || 0}</span>
                            <span><i class="fas fa-comment"></i> ${post.comments_count || 0}</span>
                        </div>
                    </div>
                </div>
                <div class="post-card-info">
                    <div class="post-card-user">
                        <img src="${post.user?.profile_picture || `https://ui-avatars.com/api/?name=${encodeURIComponent(post.user?.username || 'User')}`}" 
                             alt="${post.user?.username}">
                        <span>${post.user?.username || 'Unknown'}</span>
                    </div>
                    <p class="post-card-caption">${Utils.truncateText(post.caption || '', 60)}</p>
                    <div class="post-card-actions">
                        <button class="btn-icon" onclick="PostsManager.viewPost(${post.id})" title="View">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn-icon" onclick="PostsManager.editPost(${post.id})" title="Edit">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn-icon" onclick="PostsManager.archivePost(${post.id})" title="${post.is_archived ? 'Unarchive' : 'Archive'}">
                            <i class="fas fa-archive"></i>
                        </button>
                        <button class="btn-icon btn-danger" onclick="PostsManager.deletePost(${post.id})" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `).join('');

    // Add checkbox listeners
    document.querySelectorAll('.post-checkbox').forEach(checkbox => {
      checkbox.addEventListener('change', (e) => {
        e.stopPropagation();
        const postId = parseInt(e.target.dataset.postId);
        if (e.target.checked) {
          this.selectedPosts.add(postId);
        } else {
          this.selectedPosts.delete(postId);
        }
        this.updateBulkActions();
      });
    });
  },

  /**
   * Render posts list
   */
  renderPostsList(posts) {
    const tableBody = document.getElementById('postsTableBody');
    if (!tableBody) return;

    if (posts.length === 0) {
      tableBody.innerHTML = '<tr><td colspan="8" class="loading-cell">No posts found</td></tr>';
      return;
    }

    tableBody.innerHTML = posts.map(post => `
            <tr>
                <td>
                    <input type="checkbox" class="post-checkbox" data-post-id="${post.id}" 
                           ${this.selectedPosts.has(post.id) ? 'checked' : ''}>
                </td>
                <td>
                    <img src="${post.image || 'https://via.placeholder.com/100'}" 
                         alt="Post" 
                         style="width: 60px; height: 60px; object-fit: cover; border-radius: 8px; cursor: pointer;"
                         onclick="PostsManager.viewPost(${post.id})">
                </td>
                <td>
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <img src="${post.user?.profile_picture || `https://ui-avatars.com/api/?name=${encodeURIComponent(post.user?.username || 'User')}`}" 
                             alt="${post.user?.username}"
                             style="width: 32px; height: 32px; border-radius: 50%;">
                        <span>${post.user?.username || 'Unknown'}</span>
                    </div>
                </td>
                <td>${Utils.truncateText(post.caption || 'No caption', 50)}</td>
                <td>${post.likes_count || 0}</td>
                <td>${post.comments_count || 0}</td>
                <td>${Utils.formatDate(post.created_at)}</td>
                <td>
                    <div style="display: flex; gap: 0.25rem;">
                        <button class="btn-icon" onclick="PostsManager.viewPost(${post.id})" title="View">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn-icon" onclick="PostsManager.editPost(${post.id})" title="Edit">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn-icon" onclick="PostsManager.archivePost(${post.id})" title="${post.is_archived ? 'Unarchive' : 'Archive'}">
                            <i class="fas fa-archive"></i>
                        </button>
                        <button class="btn-icon btn-danger" onclick="PostsManager.deletePost(${post.id})" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');

    // Add checkbox listeners
    document.querySelectorAll('.post-checkbox').forEach(checkbox => {
      checkbox.addEventListener('change', (e) => {
        const postId = parseInt(e.target.dataset.postId);
        if (e.target.checked) {
          this.selectedPosts.add(postId);
        } else {
          this.selectedPosts.delete(postId);
        }
        this.updateBulkActions();
      });
    });
  },

  /**
   * View post details
   */
  async viewPost(id) {
    Modals.open('postDetailsModal');
    const body = document.getElementById('postDetailsBody');
    body.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i></div>';

    try {
      const post = await API.getPost(id);

      body.innerHTML = `
                <div class="post-details-grid">
                    <div class="post-details-image">
                        <img src="${post.image || 'https://via.placeholder.com/600'}" alt="Post">
                    </div>
                    <div class="post-details-content">
                        <div class="post-details-user">
                            <img src="${post.user?.profile_picture || `https://ui-avatars.com/api/?name=${encodeURIComponent(post.user?.username || 'User')}`}" 
                                 alt="${post.user?.username}">
                            <div>
                                <h4>${post.user?.username || 'Unknown'}</h4>
                                <p>${Utils.formatDate(post.created_at)}</p>
                            </div>
                        </div>

                        <div class="post-details-caption">
                            <p>${post.caption || 'No caption'}</p>
                            ${post.location ? `<p class="post-location"><i class="fas fa-map-marker-alt"></i> ${post.location}</p>` : ''}
                        </div>

                        <div class="post-details-stats">
                            <div class="stat-item">
                                <i class="fas fa-heart"></i>
                                <span>${post.likes_count || 0} Likes</span>
                            </div>
                            <div class="stat-item">
                                <i class="fas fa-comment"></i>
                                <span>${post.comments_count || 0} Comments</span>
                            </div>
                            <div class="stat-item">
                                <i class="fas fa-share"></i>
                                <span>${post.shares_count || 0} Shares</span>
                            </div>
                        </div>

                        <div class="post-details-actions">
                            <button class="btn-secondary" onclick="PostsManager.editPost(${post.id})">
                                <i class="fas fa-edit"></i> Edit
                            </button>
                            <button class="btn-secondary" onclick="PostsManager.archivePost(${post.id})">
                                <i class="fas fa-archive"></i> ${post.is_archived ? 'Unarchive' : 'Archive'}
                            </button>
                            <button class="btn-danger" onclick="PostsManager.deletePost(${post.id})">
                                <i class="fas fa-trash"></i> Delete
                            </button>
                        </div>
                    </div>
                </div>
            `;
    } catch (error) {
      console.error('Error loading post:', error);
      body.innerHTML = '<p style="text-align: center; color: #ef4444;">Error loading post details</p>';
    }
  },

  /**
   * Edit post
   */
  async editPost(id) {
    try {
      const post = await API.getPost(id);

      document.getElementById('editPostId').value = post.id;
      document.getElementById('editPostCaption').value = post.caption || '';
      document.getElementById('editPostLocation').value = post.location || '';

      Modals.close('postDetailsModal');
      Modals.open('editPostModal');
    } catch (error) {
      console.error('Error loading post:', error);
      Utils.showToast('Failed to load post', 'error');
    }
  },

  /**
   * Handle add post
   */
  async handleAddPost() {
    const fileInput = document.getElementById('postImageInput');
    const caption = document.getElementById('addPostCaption').value;
    const location = document.getElementById('addPostLocation').value;
    const userId = document.getElementById('addPostUser').value;

    if (!fileInput.files[0]) {
      Utils.showToast('Please select an image', 'error');
      return;
    }

    if (!userId) {
      Utils.showToast('Please select a user', 'error');
      return;
    }

    const formData = new FormData();
    formData.append('image', fileInput.files[0]);
    formData.append('caption', caption);
    formData.append('location', location);
    formData.append('user', userId);

    try {
      await API.createPost(formData);
      Utils.showToast('Post created successfully', 'success');
      Modals.close('addPostModal');
      document.getElementById('addPostForm').reset();
      document.getElementById('imagePreview').style.display = 'none';
      document.getElementById('imageUploadArea').style.display = 'flex';
      this.loadPosts();
    } catch (error) {
      console.error('Error creating post:', error);
      Utils.showToast('Failed to create post', 'error');
    }
  },

  /**
   * Handle edit post
   */
  async handleEditPost() {
    const id = document.getElementById('editPostId').value;
    const formData = {
      caption: document.getElementById('editPostCaption').value,
      location: document.getElementById('editPostLocation').value
    };

    try {
      await API.updatePost(id, formData);
      Utils.showToast('Post updated successfully', 'success');
      Modals.close('editPostModal');
      this.loadPosts();
    } catch (error) {
      console.error('Error updating post:', error);
      Utils.showToast('Failed to update post', 'error');
    }
  },

  /**
   * Delete post
   */
  async deletePost(id) {
    if (!confirm('Are you sure you want to delete this post?')) return;

    try {
      await API.deletePost(id);
      Utils.showToast('Post deleted successfully', 'success');
      Modals.close('postDetailsModal');
      this.loadPosts();
    } catch (error) {
      console.error('Error deleting post:', error);
      Utils.showToast('Failed to delete post', 'error');
    }
  },

  /**
   * Archive/Unarchive post
   */
  async archivePost(id) {
    try {
      const post = await API.getPost(id);
      await API.updatePost(id, { is_archived: !post.is_archived });
      Utils.showToast(`Post ${post.is_archived ? 'unarchived' : 'archived'} successfully`, 'success');
      this.loadPosts();
    } catch (error) {
      console.error('Error archiving post:', error);
      Utils.showToast('Failed to archive post', 'error');
    }
  },

  /**
   * Toggle select all
   */
  toggleSelectAll(checked) {
    document.querySelectorAll('.post-checkbox').forEach(checkbox => {
      checkbox.checked = checked;
      const postId = parseInt(checkbox.dataset.postId);
      if (checked) {
        this.selectedPosts.add(postId);
      } else {
        this.selectedPosts.delete(postId);
      }
    });
    this.updateBulkActions();
  },

  /**
   * Update bulk actions visibility
   */
  updateBulkActions() {
    const bulkActions = document.getElementById('postBulkActions');
    const selectedCount = document.getElementById('selectedPostsCount');

    if (this.selectedPosts.size > 0) {
      if (bulkActions) bulkActions.style.display = 'flex';
      if (selectedCount) selectedCount.textContent = this.selectedPosts.size;
    } else {
      if (bulkActions) bulkActions.style.display = 'none';
    }
  },

  /**
   * Clear selection
   */
  clearSelection() {
    this.selectedPosts.clear();
    document.querySelectorAll('.post-checkbox').forEach(cb => cb.checked = false);
    document.getElementById('selectAllPosts').checked = false;
    this.updateBulkActions();
  },

  /**
   * Handle bulk archive
   */
  async handleBulkArchive() {
    if (!confirm(`Are you sure you want to archive ${this.selectedPosts.size} posts?`)) return;

    try {
      await Promise.all(
        Array.from(this.selectedPosts).map(id =>
          API.updatePost(id, { is_archived: true })
        )
      );
      Utils.showToast(`${this.selectedPosts.size} posts archived successfully`, 'success');
      this.clearSelection();
      this.loadPosts();
    } catch (error) {
      console.error('Error archiving posts:', error);
      Utils.showToast('Failed to archive some posts', 'error');
    }
  },

  /**
   * Handle bulk delete
   */
  async handleBulkDelete() {
    if (!confirm(`Are you sure you want to delete ${this.selectedPosts.size} posts?`)) return;

    try {
      await Promise.all(
        Array.from(this.selectedPosts).map(id => API.deletePost(id))
      );
      Utils.showToast(`${this.selectedPosts.size} posts deleted successfully`, 'success');
      this.clearSelection();
      this.loadPosts();
    } catch (error) {
      console.error('Error deleting posts:', error);
      Utils.showToast('Failed to delete some posts', 'error');
    }
  },

  /**
   * Export posts
   */
  exportPosts() {
    Utils.showToast('Export feature coming soon', 'info');
  },

  /**
   * Render pagination
   */
  renderPagination(response) {
    const pagination = document.getElementById('postsPagination');
    if (!pagination || !response.count) return;

    const totalPages = Math.ceil(response.count / this.perPage);
    if (totalPages <= 1) {
      pagination.innerHTML = '';
      return;
    }

    let html = '<div class="pagination">';

    // Previous button
    html += `<button class="pagination-btn" ${this.currentPage === 1 ? 'disabled' : ''} 
                 onclick="PostsManager.goToPage(${this.currentPage - 1})">
                 <i class="fas fa-chevron-left"></i>
                 </button>`;

    // Page numbers
    for (let i = 1; i <= Math.min(totalPages, 5); i++) {
      html += `<button class="pagination-btn ${i === this.currentPage ? 'active' : ''}" 
                     onclick="PostsManager.goToPage(${i})">${i}</button>`;
    }

    // Next button
    html += `<button class="pagination-btn" ${this.currentPage === totalPages ? 'disabled' : ''} 
                 onclick="PostsManager.goToPage(${this.currentPage + 1})">
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
    this.loadPosts();
  }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
  module.exports = PostsManager;
}
