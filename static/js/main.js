// AutoCare Global Client Engine

// 1. Theme Management (Dark / Light Mode)
(function initTheme() {
  const savedTheme = localStorage.getItem('autocare_theme') || 'light';
  document.documentElement.setAttribute('data-theme', savedTheme);
  updateThemeIcons(savedTheme);
})();

function toggleTheme() {
  const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
  const newTheme = currentTheme === 'light' ? 'dark' : 'light';
  document.documentElement.setAttribute('data-theme', newTheme);
  localStorage.setItem('autocare_theme', newTheme);
  updateThemeIcons(newTheme);
}

function updateThemeIcons(theme) {
  const toggleBtns = document.querySelectorAll('.theme-toggle-btn');
  toggleBtns.forEach(btn => {
    btn.innerHTML = theme === 'dark' ? '☀️' : '🌙';
    btn.setAttribute('title', theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode');
  });
}

// 2. Toast Notification Engine
function showToast(message, type = 'info', duration = 4000) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;

  const icons = {
    success: '✓',
    error: '✕',
    warning: '⚠',
    info: 'ℹ'
  };

  const titles = {
    success: 'Success',
    error: 'Error',
    warning: 'Notice',
    info: 'Information'
  };

  toast.innerHTML = `
    <span class="toast-icon">${icons[type] || 'ℹ'}</span>
    <div class="toast-body">
      <div class="toast-title">${titles[type] || 'Notice'}</div>
      <div class="toast-message">${escapeHtml(message)}</div>
    </div>
    <button class="toast-close" onclick="dismissToast(this.parentElement)">&times;</button>
  `;

  container.appendChild(toast);

  const timer = setTimeout(() => {
    dismissToast(toast);
  }, duration);

  toast.dataset.timerId = timer;
}

function dismissToast(toast) {
  if (!toast) return;
  clearTimeout(toast.dataset.timerId);
  toast.classList.add('toast-hiding');
  setTimeout(() => {
    if (toast.parentElement) {
      toast.parentElement.removeChild(toast);
    }
  }, 300);
}

// 3. Modal Manager
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('active');
    document.body.style.overflow = '';
  }
}

// Close modal when clicking on backdrop
document.addEventListener('click', (e) => {
  if (e.target.classList.contains('modal-backdrop')) {
    e.target.classList.remove('active');
    document.body.style.overflow = '';
  }
});

// 4. Interactive Confirmation Dialog
let activeConfirmCallback = null;

function showConfirmDialog({ title, message, confirmText = 'Confirm', confirmBtnClass = 'btn-danger', onConfirm }) {
  const dialog = document.getElementById('global-confirm-modal');
  if (!dialog) return;

  document.getElementById('confirm-modal-title').textContent = title;
  document.getElementById('confirm-modal-message').textContent = message;
  const confirmBtn = document.getElementById('confirm-modal-btn');
  confirmBtn.textContent = confirmText;
  confirmBtn.className = `btn ${confirmBtnClass}`;

  activeConfirmCallback = onConfirm;
  openModal('global-confirm-modal');
}

function handleConfirmAction() {
  if (typeof activeConfirmCallback === 'function') {
    activeConfirmCallback();
  }
  closeModal('global-confirm-modal');
  activeConfirmCallback = null;
}

// 5. Sidebar & Mobile Navigation
function toggleSidebar() {
  const sidebar = document.querySelector('.sidebar');
  if (sidebar) {
    sidebar.classList.toggle('open');
  }
}

// 6. Notification Center Interactions
function toggleNotificationDropdown() {
  const menu = document.getElementById('notif-menu');
  if (menu) {
    menu.classList.toggle('show');
  }
}

// Close notification menu on click outside
document.addEventListener('click', (e) => {
  const notifWrapper = document.querySelector('.notif-dropdown-wrapper');
  if (notifWrapper && !notifWrapper.contains(e.target)) {
    const menu = document.getElementById('notif-menu');
    if (menu) menu.classList.remove('show');
  }
});

async function markNotificationAsRead(notifId, redirectUrl = null) {
  try {
    const res = await fetch(`/api/notifications/read/${notifId}`, { method: 'POST' });
    if (res.ok && redirectUrl) {
      window.location.href = redirectUrl;
    } else {
      window.location.reload();
    }
  } catch (err) {
    if (redirectUrl) window.location.href = redirectUrl;
  }
}

async function markAllNotificationsRead() {
  try {
    const res = await fetch('/api/notifications/read-all', { method: 'POST' });
    if (res.ok) {
      showToast('All notifications marked as read', 'success');
      setTimeout(() => window.location.reload(), 600);
    }
  } catch (err) {
    showToast('Failed to update notifications', 'error');
  }
}

// 7. Security / Helper Utilities
function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// 8. Universal Table Search & Filter
function filterTable(inputId, tableId) {
  const input = document.getElementById(inputId);
  if (!input) return;
  const filter = input.value.toLowerCase();
  const table = document.getElementById(tableId);
  if (!table) return;

  const tbody = table.getElementsByTagName('tbody')[0];
  if (!tbody) return;
  const rows = tbody.getElementsByTagName('tr');
  for (let i = 0; i < rows.length; i++) {
    const text = rows[i].textContent.toLowerCase();
    rows[i].style.display = text.includes(filter) ? '' : 'none';
  }
}

// Auto-dismiss Django/Flask flashed messages into modern toasts
document.addEventListener('DOMContentLoaded', () => {
  const flashedElements = document.querySelectorAll('.flask-flash-msg');
  flashedElements.forEach(el => {
    const category = el.dataset.category || 'info';
    const message = el.textContent.trim();
    if (message) {
      showToast(message, category === 'message' ? 'info' : category);
    }
  });

  // Mobile menu button for public navbar
  const mobileNavToggle = document.getElementById('public-mobile-nav-toggle');
  const mobileNavMenu = document.getElementById('public-nav-links');
  if (mobileNavToggle && mobileNavMenu) {
    mobileNavToggle.addEventListener('click', () => {
      mobileNavMenu.classList.toggle('active');
    });

    // Close menu when clicking a link
    mobileNavMenu.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => {
        mobileNavMenu.classList.remove('active');
      });
    });
  }
});

