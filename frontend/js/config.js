/* Config & API Constants */
const CONFIG = {
  API_BASE_URL: 'http://localhost:5000/api',
  STORAGE_KEYS: {
    TOKEN: 'skin_portal_token',
    USER: 'skin_portal_user',
    IS_ADMIN: 'skin_portal_is_admin',
    LAST_RESULT: 'skin_portal_last_result'
  }
};

// Helper utilities
const Utils = {
  getToken: () => localStorage.getItem(CONFIG.STORAGE_KEYS.TOKEN),
  getUser: () => {
    const raw = localStorage.getItem(CONFIG.STORAGE_KEYS.USER);
    return raw ? JSON.parse(raw) : null;
  },
  setUserSession: (token, user, isAdmin = false) => {
    localStorage.setItem(CONFIG.STORAGE_KEYS.TOKEN, token);
    localStorage.setItem(CONFIG.STORAGE_KEYS.USER, JSON.stringify(user));
    localStorage.setItem(CONFIG.STORAGE_KEYS.IS_ADMIN, isAdmin ? 'true' : 'false');
  },
  clearSession: () => {
    localStorage.removeItem(CONFIG.STORAGE_KEYS.TOKEN);
    localStorage.removeItem(CONFIG.STORAGE_KEYS.USER);
    localStorage.removeItem(CONFIG.STORAGE_KEYS.IS_ADMIN);
  },
  isAuthenticated: () => !!Utils.getToken(),
  isAdmin: () => localStorage.getItem(CONFIG.STORAGE_KEYS.IS_ADMIN) === 'true',
  
  formatDate: (dateStr) => {
    if (!dateStr) return 'N/A';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  },

  showAlert: (message, type = 'error') => {
    const alertBox = document.createElement('div');
    alertBox.className = `alert alert-${type}`;
    alertBox.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      z-index: 9999;
      padding: 1rem 1.5rem;
      border-radius: 12px;
      color: #fff;
      background-color: ${type === 'error' ? '#ef4444' : type === 'success' ? '#10b981' : '#0284c7'};
      box-shadow: 0 10px 25px rgba(0,0,0,0.15);
      font-weight: 600;
      animation: fadeIn 0.3s ease;
    `;
    alertBox.innerText = message;
    document.body.appendChild(alertBox);
    setTimeout(() => {
      alertBox.remove();
    }, 4000);
  }
};
