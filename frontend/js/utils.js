/* ============================================
   PhytoSentinel - Shared Utilities
   ============================================ */

// API Configuration
const API_BASE_URL = 'http://localhost:8000/api';

// ============================================
// API SERVICE
// ============================================

const ApiService = {
  // Generic fetch wrapper
  async request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const defaultOptions = {
      headers: {
        'Content-Type': 'application/json',
      },
    };

    const config = { ...defaultOptions, ...options };

    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        const error = await response.json().catch(() => ({ message: 'Request failed' }));
        throw new Error(error.message || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API Error [${endpoint}]:`, error);
      throw error;
    }
  },

  // GET request
  async get(endpoint) {
    return this.request(endpoint, { method: 'GET' });
  },

  // POST request
  async post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // PUT request
  async put(endpoint, data) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  // DELETE request
  async delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  },

  // Upload file
  async uploadFile(endpoint, formData) {
    const url = `${API_BASE_URL}${endpoint}`;

    try {
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ message: 'Upload failed' }));
        throw new Error(error.message || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`Upload Error [${endpoint}]:`, error);
      throw error;
    }
  },
};

// ============================================
// SIDEBAR MANAGEMENT
// ============================================

const Sidebar = {
  isCollapsed: false,

  init() {
    this.sidebar = document.querySelector('.sidebar');
    this.toggleBtn = document.querySelector('.sidebar-toggle');
    this.mobileToggle = document.querySelector('.mobile-menu-toggle');

    if (this.toggleBtn) {
      this.toggleBtn.addEventListener('click', () => this.toggle());
    }

    if (this.mobileToggle) {
      this.mobileToggle.addEventListener('click', () => this.toggleMobile());
    }

    // Highlight active nav item based on URL
    this.highlightActive();
  },

  toggle() {
    this.isCollapsed = !this.isCollapsed;
    this.sidebar?.classList.toggle('collapsed', this.isCollapsed);
    localStorage.setItem('sidebarCollapsed', this.isCollapsed);
  },

  toggleMobile() {
    this.sidebar?.classList.toggle('mobile-open');
  },

  highlightActive() {
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    const navItems = document.querySelectorAll('.nav-item');

    navItems.forEach(item => {
      const href = item.getAttribute('href');
      if (href === currentPage || (currentPage === '' && href === 'index.html')) {
        item.classList.add('active');
      }
    });
  },

  restoreState() {
    const saved = localStorage.getItem('sidebarCollapsed');
    if (saved === 'true') {
      this.isCollapsed = true;
      this.sidebar?.classList.add('collapsed');
    }
  },
};

// ============================================
// NOTIFICATIONS
// ============================================

const Notifications = {
  container: null,

  init() {
    this.container = document.getElementById('notificationContainer') || this.createContainer();
  },

  createContainer() {
    const container = document.createElement('div');
    container.id = 'notificationContainer';
    container.style.cssText = `
      position: fixed;
      top: 80px;
      right: 20px;
      z-index: 9999;
      display: flex;
      flex-direction: column;
      gap: 10px;
      max-width: 380px;
    `;
    document.body.appendChild(container);
    return container;
  },

  show(message, type = 'info', duration = 5000) {
    const notification = document.createElement('div');
    const colors = {
      success: { bg: 'rgba(74, 222, 128, 0.12)', border: 'rgba(74, 222, 128, 0.4)', icon: '✓' },
      error: { bg: 'rgba(248, 113, 113, 0.12)', border: 'rgba(248, 113, 113, 0.4)', icon: '✕' },
      warning: { bg: 'rgba(251, 191, 36, 0.12)', border: 'rgba(251, 191, 36, 0.4)', icon: '⚠' },
      info: { bg: 'rgba(45, 212, 191, 0.12)', border: 'rgba(45, 212, 191, 0.4)', icon: 'ℹ' },
    };

    const style = colors[type] || colors.info;

    notification.style.cssText = `
      background: ${style.bg};
      border: 1px solid ${style.border};
      border-radius: 12px;
      padding: 14px 18px;
      display: flex;
      align-items: center;
      gap: 12px;
      animation: slideIn 0.3s ease;
      backdrop-filter: blur(10px);
    `;

    notification.innerHTML = `
      <span style="font-size: 18px; color: var(--${type === 'success' ? 'green' : type === 'error' ? 'red' : type === 'warning' ? 'amber' : 'teal'});">${style.icon}</span>
      <span style="color: var(--t2); font-size: 13px; flex: 1;">${message}</span>
    `;

    this.container.appendChild(notification);

    setTimeout(() => {
      notification.style.animation = 'fadeIn 0.3s ease reverse';
      setTimeout(() => notification.remove(), 300);
    }, duration);
  },

  success(message) { this.show(message, 'success'); },
  error(message) { this.show(message, 'error'); },
  warning(message) { this.show(message, 'warning'); },
  info(message) { this.show(message, 'info'); },
};

// ============================================
// MODAL MANAGEMENT
// ============================================

const Modal = {
  show(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.add('active');
      document.body.style.overflow = 'hidden';
    }
  },

  hide(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.remove('active');
      document.body.style.overflow = '';
    }
  },

  init() {
    document.querySelectorAll('.modal-overlay').forEach(modal => {
      const closeBtn = modal.querySelector('.modal-close');
      if (closeBtn) {
        closeBtn.addEventListener('click', () => this.hide(modal.id));
      }
      modal.addEventListener('click', (e) => {
        if (e.target === modal) this.hide(modal.id);
      });
    });
  },
};

// ============================================
// FORM HANDLING
// ============================================

const Forms = {
  async submit(formId, apiEndpoint, successCallback) {
    const form = document.getElementById(formId);
    if (!form) return;

    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    try {
      const result = await ApiService.post(apiEndpoint, data);
      Notifications.success('Opération réussie!');
      if (successCallback) successCallback(result);
      return result;
    } catch (error) {
      Notifications.error(error.message || 'Une erreur est survenue');
      throw error;
    }
  },

  async upload(formId, apiEndpoint, fileInputName, successCallback) {
    const form = document.getElementById(formId);
    if (!form) return;

    const fileInput = form.querySelector(`[name="${fileInputName}"]`);
    if (!fileInput || !fileInput.files[0]) {
      Notifications.warning('Veuillez sélectionner un fichier');
      return;
    }

    const formData = new FormData();
    formData.append(fileInputName, fileInput.files[0]);

    // Add other form fields
    const formDataEntries = new FormData(form);
    for (let [key, value] of formDataEntries.entries()) {
      if (key !== fileInputName) {
        formData.append(key, value);
      }
    }

    try {
      const result = await ApiService.uploadFile(apiEndpoint, formData);
      Notifications.success('Fichier uploaded avec succès!');
      if (successCallback) successCallback(result);
      return result;
    } catch (error) {
      Notifications.error(error.message || "Échec de l'upload");
      throw error;
    }
  },

  clear(formId) {
    const form = document.getElementById(formId);
    if (form) form.reset();
  },
};

// ============================================
// DATA TABLES
// ============================================

const DataTable = {
  create(tableId, columns, data, options = {}) {
    const table = document.getElementById(tableId);
    if (!table) return;

    // Create table header
    const thead = table.querySelector('thead');
    if (thead) {
      thead.innerHTML = `
        <tr>
          ${columns.map(col => `<th>${col.label}</th>`).join('')}
          ${options.actions ? '<th>Actions</th>' : ''}
        </tr>
      `;
    }

    // Create table body
    const tbody = table.querySelector('tbody');
    if (tbody) {
      if (data.length === 0) {
        tbody.innerHTML = `
          <tr>
            <td colspan="${columns.length + (options.actions ? 1 : 0)}" class="text-center" style="padding: 40px;">
              <div class="empty-state">
                <div class="empty-state-icon">📭</div>
                <div class="empty-state-title">Aucune donnée</div>
                <div class="empty-state-text">Les données apparaîtront ici</div>
              </div>
            </td>
          </tr>
        `;
      } else {
        tbody.innerHTML = data.map(row => `
          <tr>
            ${columns.map(col => `<td>${col.render ? col.render(row[col.key]) : row[col.key]}</td>`).join('')}
            ${options.actions ? `<td>${options.actions(row)}</td>` : ''}
          </tr>
        `).join('');
      }
    }
  },

  update(tableId, data, columns, options = {}) {
    this.create(tableId, columns, data, options);
  },
};

// ============================================
// CHARTS HELPERS
// ============================================

const Charts = {
  // Create a simple bar chart
  barChart(containerId, data, options = {}) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const maxValue = Math.max(...data.map(d => d.value));
    const height = options.height || 120;

    container.innerHTML = `
      <div style="display: flex; gap: 8px; align-items: flex-end; height: ${height}px; padding-bottom: 8px;">
        ${data.map(item => {
          const percent = (item.value / maxValue) * 100;
          return `
            <div style="flex: 1; display: flex; flex-direction: column; align-items: center; gap: 6px; height: 100%; justify-content: flex-end;">
              <div style="width: 100%; background: ${item.color || 'var(--green)'}; border-radius: 4px 4px 0 0; height: ${percent}%; transition: height 1s ease;"></div>
              <div style="font-size: 10px; color: var(--t3);">${item.label}</div>
            </div>
          `;
        }).join('')}
      </div>
    `;
  },

  // Create progress ring
  progressRing(containerId, percent, options = {}) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const size = options.size || 80;
    const stroke = options.stroke || 8;
    const radius = (size - stroke) / 2;
    const circumference = radius * 2 * Math.PI;
    const offset = circumference - (percent / 100) * circumference;

    container.innerHTML = `
      <svg width="${size}" height="${size}" style="transform: rotate(-90deg);">
        <circle cx="${size/2}" cy="${size/2}" r="${radius}" fill="none" stroke="rgba(74, 222, 128, 0.1)" stroke-width="${stroke}"/>
        <circle cx="${size/2}" cy="${size/2}" r="${radius}" fill="none" stroke="${options.color || 'var(--green)'}" stroke-width="${stroke}"
          stroke-dasharray="${circumference}" stroke-dashoffset="${offset}" stroke-linecap="round" style="transition: stroke-dashoffset 1s ease;"/>
      </svg>
      <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center;">
        <div style="font-size: ${size/4}px; font-weight: 800; color: var(--t1);">${percent}%</div>
      </div>
    `;
  },
};

// ============================================
// COUNTER ANIMATION
// ============================================

function animateCounter(element, target, duration = 1800) {
  const t0 = performance.now();

  function tick(now) {
    const progress = Math.min((now - t0) / duration, 1);
    const ease = 1 - Math.pow(1 - progress, 3);
    element.textContent = Math.floor(ease * target);

    if (progress < 1) {
      requestAnimationFrame(tick);
    } else {
      element.textContent = target;
    }
  }

  requestAnimationFrame(tick);
}

// Initialize counters when they come into view
const counterObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const target = parseInt(entry.target.getAttribute('data-count'));
      animateCounter(entry.target, target);
      counterObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.5 });

document.querySelectorAll('[data-count]').forEach(el => counterObserver.observe(el));

// ============================================
// REVEAL ON SCROLL
// ============================================

const revealObserver = new IntersectionObserver((entries) => {
  entries.forEach((entry, index) => {
    if (entry.isIntersecting) {
      setTimeout(() => {
        entry.target.classList.add('visible');
        entry.target.style.opacity = '1';
        entry.target.style.transform = 'translateY(0)';
      }, index * 80);
    }
  });
}, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

document.querySelectorAll('.reveal').forEach(el => {
  el.style.opacity = '0';
  el.style.transform = 'translateY(28px)';
  el.style.transition = 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
  revealObserver.observe(el);
});

// ============================================
// UTILITY FUNCTIONS
// ============================================

// Format date
function formatDate(date, locale = 'fr-FR') {
  return new Date(date).toLocaleDateString(locale, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

// Format date time
function formatDateTime(date, locale = 'fr-FR') {
  return new Date(date).toLocaleString(locale, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

// Time ago
function timeAgo(date) {
  const seconds = Math.floor((new Date() - new Date(date)) / 1000);

  const intervals = {
    année: 31536000,
    mois: 2592000,
    semaine: 604800,
    jour: 86400,
    heure: 3600,
    minute: 60,
  };

  for (const [name, secondsInUnit] of Object.entries(intervals)) {
    const interval = Math.floor(seconds / secondsInUnit);
    if (interval >= 1) {
      return `il y a ${interval} ${name}${interval > 1 ? 's' : ''}`;
    }
  }
  return 'à l\'instant';
}

// Debounce
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// Generate ID
function generateId() {
  return Date.now().toString(36) + Math.random().toString(36).substr(2);
}

// ============================================
// EXPORT
// ============================================

window.PhytoSentinel = {
  ApiService,
  Sidebar,
  Notifications,
  Modal,
  Forms,
  DataTable,
  Charts,
  animateCounter,
  formatDate,
  formatDateTime,
  timeAgo,
  debounce,
  generateId,
};

// ============================================
// INITIALIZE ON DOM READY
// ============================================

document.addEventListener('DOMContentLoaded', () => {
  Sidebar.init();
  Sidebar.restoreState();
  Modal.init();
});

// ============================================
// GLOBAL ERROR HANDLER
// ============================================

window.addEventListener('error', (event) => {
  console.error('Global error:', event.error);
  Notifications.error('Une erreur inattendue est survenue');
});
