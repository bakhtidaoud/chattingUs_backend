/**
 * Modal Management
 * Handles opening/closing modals
 */

const Modals = {
  /**
   * Open modal
   * @param {string} modalId - Modal ID
   */
  open(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.add('active');
      document.body.style.overflow = 'hidden';
    }
  },

  /**
   * Close modal
   * @param {string} modalId - Modal ID
   */
  close(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.remove('active');
      document.body.style.overflow = '';
    }
  },

  /**
   * Initialize modal event listeners
   */
  init() {
    // Close buttons
    document.querySelectorAll('.modal-close, [data-modal]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        const modalId = btn.dataset.modal;
        if (modalId) {
          this.close(modalId);
        }
      });
    });

    // Click outside to close
    document.querySelectorAll('.modal').forEach(modal => {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) {
          this.close(modal.id);
        }
      });
    });

    // ESC key to close
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        document.querySelectorAll('.modal.active').forEach(modal => {
          this.close(modal.id);
        });
      }
    });
  }
};

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
  Modals.init();
});

// Export
if (typeof module !== 'undefined' && module.exports) {
  module.exports = Modals;
}
