/**
 * Performance Optimization Module
 * Maximize dashboard performance with caching, lazy loading, and optimization
 */

const PerformanceOptimizer = {
  // ============================================
  // API CACHING
  // ============================================

  cache: {
    storage: new Map(),
    ttl: 5 * 60 * 1000, // 5 minutes

    set(key, data) {
      this.storage.set(key, {
        data,
        timestamp: Date.now()
      });
    },

    get(key) {
      const cached = this.storage.get(key);
      if (!cached) return null;

      const age = Date.now() - cached.timestamp;
      if (age > this.ttl) {
        this.storage.delete(key);
        return null;
      }

      return cached.data;
    },

    clear() {
      this.storage.clear();
    },

    invalidate(pattern) {
      for (const key of this.storage.keys()) {
        if (key.includes(pattern)) {
          this.storage.delete(key);
        }
      }
    }
  },

  // ============================================
  // LAZY LOADING
  // ============================================

  lazyLoad: {
    imageObserver: null,

    init() {
      this.setupImageLazyLoading();
      this.setupModuleLazyLoading();
    },

    setupImageLazyLoading() {
      if ('IntersectionObserver' in window) {
        this.imageObserver = new IntersectionObserver((entries) => {
          entries.forEach(entry => {
            if (entry.isIntersecting) {
              const img = entry.target;
              this.loadImage(img);
              this.imageObserver.unobserve(img);
            }
          });
        }, {
          rootMargin: '50px'
        });

        this.observeImages();
      } else {
        // Fallback for older browsers
        this.loadAllImages();
      }
    },

    observeImages() {
      document.querySelectorAll('img[data-src]').forEach(img => {
        this.imageObserver.observe(img);
      });
    },

    loadImage(img) {
      const src = img.dataset.src;
      const srcset = img.dataset.srcset;

      if (src) {
        img.src = src;
        img.removeAttribute('data-src');
      }

      if (srcset) {
        img.srcset = srcset;
        img.removeAttribute('data-srcset');
      }

      img.classList.add('loaded');
    },

    loadAllImages() {
      document.querySelectorAll('img[data-src]').forEach(img => {
        this.loadImage(img);
      });
    },

    setupModuleLazyLoading() {
      // Lazy load page modules
      window.loadModule = async (moduleName) => {
        if (window[moduleName]) return window[moduleName];

        try {
          const module = await import(`./js/${moduleName}.js`);
          window[moduleName] = module.default || module;
          return window[moduleName];
        } catch (error) {
          console.error(`Failed to load module ${moduleName}:`, error);
          return null;
        }
      };
    }
  },

  // ============================================
  // VIRTUAL SCROLLING
  // ============================================

  virtualScroll: {
    itemHeight: 60,
    visibleItems: 20,
    buffer: 5,

    init(container, items, renderItem) {
      const viewport = container.querySelector('.virtual-scroll-viewport');
      const content = container.querySelector('.virtual-scroll-content');

      if (!viewport || !content) return;

      const totalHeight = items.length * this.itemHeight;
      content.style.height = `${totalHeight}px`;

      let scrollTop = 0;

      viewport.addEventListener('scroll', () => {
        scrollTop = viewport.scrollTop;
        this.render(viewport, content, items, renderItem, scrollTop);
      });

      // Initial render
      this.render(viewport, content, items, renderItem, scrollTop);
    },

    render(viewport, content, items, renderItem, scrollTop) {
      const startIndex = Math.floor(scrollTop / this.itemHeight) - this.buffer;
      const endIndex = startIndex + this.visibleItems + (this.buffer * 2);

      const visibleItems = items.slice(
        Math.max(0, startIndex),
        Math.min(items.length, endIndex)
      );

      content.innerHTML = visibleItems.map((item, index) => {
        const actualIndex = Math.max(0, startIndex) + index;
        const top = actualIndex * this.itemHeight;
        return `
                    <div class="virtual-item" style="position: absolute; top: ${top}px; height: ${this.itemHeight}px; width: 100%;">
                        ${renderItem(item)}
                    </div>
                `;
      }).join('');
    }
  },

  // ============================================
  // REQUEST OPTIMIZATION
  // ============================================

  requests: {
    pending: new Map(),
    abortControllers: new Map(),

    async optimizedFetch(url, options = {}) {
      // Check cache first
      const cacheKey = `${url}${JSON.stringify(options)}`;
      const cached = PerformanceOptimizer.cache.get(cacheKey);
      if (cached) return cached;

      // Cancel duplicate requests
      if (this.pending.has(cacheKey)) {
        return this.pending.get(cacheKey);
      }

      // Create abort controller
      const controller = new AbortController();
      this.abortControllers.set(cacheKey, controller);

      const promise = fetch(url, {
        ...options,
        signal: controller.signal
      })
        .then(response => response.json())
        .then(data => {
          PerformanceOptimizer.cache.set(cacheKey, data);
          this.pending.delete(cacheKey);
          this.abortControllers.delete(cacheKey);
          return data;
        })
        .catch(error => {
          this.pending.delete(cacheKey);
          this.abortControllers.delete(cacheKey);
          throw error;
        });

      this.pending.set(cacheKey, promise);
      return promise;
    },

    cancelRequest(url) {
      const controller = this.abortControllers.get(url);
      if (controller) {
        controller.abort();
        this.abortControllers.delete(url);
        this.pending.delete(url);
      }
    },

    cancelAllRequests() {
      this.abortControllers.forEach(controller => controller.abort());
      this.abortControllers.clear();
      this.pending.clear();
    }
  },

  // ============================================
  // MEMORY MANAGEMENT
  // ============================================

  memory: {
    listeners: new Map(),
    intervals: new Set(),
    timeouts: new Set(),

    addEventListener(element, event, handler) {
      element.addEventListener(event, handler);

      if (!this.listeners.has(element)) {
        this.listeners.set(element, []);
      }
      this.listeners.get(element).push({ event, handler });
    },

    setInterval(callback, delay) {
      const id = setInterval(callback, delay);
      this.intervals.add(id);
      return id;
    },

    setTimeout(callback, delay) {
      const id = setTimeout(() => {
        callback();
        this.timeouts.delete(id);
      }, delay);
      this.timeouts.add(id);
      return id;
    },

    cleanup() {
      // Remove event listeners
      this.listeners.forEach((handlers, element) => {
        handlers.forEach(({ event, handler }) => {
          element.removeEventListener(event, handler);
        });
      });
      this.listeners.clear();

      // Clear intervals
      this.intervals.forEach(id => clearInterval(id));
      this.intervals.clear();

      // Clear timeouts
      this.timeouts.forEach(id => clearTimeout(id));
      this.timeouts.clear();

      // Cancel pending requests
      PerformanceOptimizer.requests.cancelAllRequests();

      // Clear cache
      PerformanceOptimizer.cache.clear();
    }
  },

  // ============================================
  // DEBOUNCE & THROTTLE
  // ============================================

  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  },

  throttle(func, limit) {
    let inThrottle;
    return function (...args) {
      if (!inThrottle) {
        func.apply(this, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  },

  // ============================================
  // PERFORMANCE MONITORING
  // ============================================

  monitor: {
    metrics: {
      pageLoadTime: 0,
      apiCalls: 0,
      cacheHits: 0,
      cacheMisses: 0,
      errors: 0
    },

    init() {
      this.measurePageLoad();
      this.setupErrorTracking();
      this.setupPerformanceObserver();
    },

    measurePageLoad() {
      window.addEventListener('load', () => {
        const perfData = performance.timing;
        const pageLoadTime = perfData.loadEventEnd - perfData.navigationStart;
        this.metrics.pageLoadTime = pageLoadTime;

        console.log(`Page load time: ${pageLoadTime}ms`);

        // Send to analytics
        this.sendMetric('page_load', pageLoadTime);
      });
    },

    setupErrorTracking() {
      window.addEventListener('error', (event) => {
        this.metrics.errors++;
        this.logError({
          message: event.message,
          filename: event.filename,
          lineno: event.lineno,
          colno: event.colno
        });
      });

      window.addEventListener('unhandledrejection', (event) => {
        this.metrics.errors++;
        this.logError({
          message: 'Unhandled Promise Rejection',
          reason: event.reason
        });
      });
    },

    setupPerformanceObserver() {
      if ('PerformanceObserver' in window) {
        // Observe long tasks
        const observer = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (entry.duration > 50) {
              console.warn('Long task detected:', entry);
            }
          }
        });

        try {
          observer.observe({ entryTypes: ['longtask'] });
        } catch (e) {
          // longtask not supported
        }
      }
    },

    logError(error) {
      console.error('Error tracked:', error);
      // Send to error tracking service
      this.sendMetric('error', error);
    },

    sendMetric(name, value) {
      // Send to analytics service
      if (window.gtag) {
        gtag('event', name, { value });
      }
    },

    getMetrics() {
      return {
        ...this.metrics,
        memory: performance.memory ? {
          used: performance.memory.usedJSHeapSize,
          total: performance.memory.totalJSHeapSize,
          limit: performance.memory.jsHeapSizeLimit
        } : null
      };
    }
  },

  // ============================================
  // RESOURCE HINTS
  // ============================================

  resourceHints: {
    preload(url, as) {
      const link = document.createElement('link');
      link.rel = 'preload';
      link.href = url;
      link.as = as;
      document.head.appendChild(link);
    },

    prefetch(url) {
      const link = document.createElement('link');
      link.rel = 'prefetch';
      link.href = url;
      document.head.appendChild(link);
    },

    preconnect(url) {
      const link = document.createElement('link');
      link.rel = 'preconnect';
      link.href = url;
      document.head.appendChild(link);
    },

    setupHints() {
      // Preconnect to API
      this.preconnect('http://localhost:8000');

      // Preload critical fonts
      this.preload('/fonts/inter.woff2', 'font');

      // Prefetch next likely pages
      this.prefetch('/admin-dashboard/users.html');
    }
  },

  // ============================================
  // IMAGE OPTIMIZATION
  // ============================================

  images: {
    generateSrcSet(url, sizes = [320, 640, 1024, 1920]) {
      return sizes.map(size => `${url}?w=${size} ${size}w`).join(', ');
    },

    generateSizes() {
      return '(max-width: 768px) 100vw, (max-width: 1024px) 50vw, 33vw';
    },

    createResponsiveImage(url, alt) {
      return `
                <img 
                    data-src="${url}"
                    data-srcset="${this.generateSrcSet(url)}"
                    sizes="${this.generateSizes()}"
                    alt="${alt}"
                    loading="lazy"
                    decoding="async"
                >
            `;
    },

    supportsWebP() {
      const canvas = document.createElement('canvas');
      return canvas.toDataURL('image/webp').indexOf('data:image/webp') === 0;
    }
  },

  // ============================================
  // INITIALIZATION
  // ============================================

  init() {
    this.lazyLoad.init();
    this.monitor.init();
    this.resourceHints.setupHints();

    // Cleanup on page unload
    window.addEventListener('beforeunload', () => {
      this.memory.cleanup();
    });

    console.log('Performance Optimizer initialized');
  }
};

// Auto-initialize
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => PerformanceOptimizer.init());
} else {
  PerformanceOptimizer.init();
}

// Export
if (typeof module !== 'undefined' && module.exports) {
  module.exports = PerformanceOptimizer;
}
