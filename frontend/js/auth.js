/* Auth JS - Registration, Login, Session Management */
document.addEventListener('DOMContentLoaded', () => {
  setupNavbar();
  setupAuthForms();
});

function setupNavbar() {
  const user = Utils.getUser();
  const token = Utils.getToken();
  const navActions = document.getElementById('nav-actions');

  if (navActions) {
    if (token && user) {
      navActions.innerHTML = `
        <div style="display:flex; align-items:center; gap: 1rem;">
          <span style="font-weight: 600; color: var(--slate-700);">Hi, ${user.full_name || user.username || 'User'}</span>
          <a href="${Utils.isAdmin() ? 'admin.html' : 'dashboard.html'}" class="btn btn-sm btn-primary">Dashboard</a>
          <button id="logout-btn" class="btn btn-sm btn-outline">Logout</button>
        </div>
      `;
      document.getElementById('logout-btn')?.addEventListener('click', () => {
        Utils.clearSession();
        window.location.href = 'login.html';
      });
    } else {
      navActions.innerHTML = `
        <a href="login.html" class="btn btn-sm btn-outline">Sign In</a>
        <a href="register.html" class="btn btn-sm btn-primary">Register</a>
      `;
    }
  }
}

function setupAuthForms() {
  // Login Form
  const loginForm = document.getElementById('login-form');
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = document.getElementById('email').value.trim();
      const password = document.getElementById('password').value;
      const role = document.getElementById('user-role')?.value || 'user';

      if (!email || !password) {
        Utils.showAlert('Please fill in all fields.');
        return;
      }

      try {
        const endpoint = role === 'admin' ? '/auth/admin-login' : '/auth/login';
        const response = await fetch(`${CONFIG.API_BASE_URL}${endpoint}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(role === 'admin' ? { username: email, password } : { email, password })
        });

        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.message || 'Login failed. Please check credentials.');
        }

        Utils.setUserSession(data.token, data.user, role === 'admin');
        Utils.showAlert('Login successful!', 'success');
        
        setTimeout(() => {
          window.location.href = role === 'admin' ? 'admin.html' : 'dashboard.html';
        }, 1000);

      } catch (err) {
        Utils.showAlert(err.message);
      }
    });
  }

  // Register Form
  const registerForm = document.getElementById('register-form');
  if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const full_name = document.getElementById('full_name').value.trim();
      const email = document.getElementById('email').value.trim();
      const phone = document.getElementById('phone').value.trim();
      const password = document.getElementById('password').value;
      const confirmPassword = document.getElementById('confirm_password').value;

      if (!full_name || !email || !password) {
        Utils.showAlert('Full Name, Email, and Password are required.');
        return;
      }

      if (password !== confirmPassword) {
        Utils.showAlert('Passwords do not match.');
        return;
      }

      try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ full_name, email, phone, password })
        });

        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.message || 'Registration failed.');
        }

        Utils.showAlert('Registration successful! Please sign in.', 'success');
        setTimeout(() => {
          window.location.href = 'login.html';
        }, 1200);

      } catch (err) {
        Utils.showAlert(err.message);
      }
    });
  }
}
