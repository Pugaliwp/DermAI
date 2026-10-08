/* User Profile Controller */
document.addEventListener('DOMContentLoaded', () => {
  if (!Utils.isAuthenticated()) {
    window.location.href = 'login.html';
    return;
  }

  loadUserProfile();
  setupProfileForm();
});

function loadUserProfile() {
  const user = Utils.getUser();
  if (!user) return;

  document.getElementById('profile-full-name').value = user.full_name || '';
  document.getElementById('profile-email').value = user.email || '';
  document.getElementById('profile-phone').value = user.phone || '';
  
  document.getElementById('display-name').textContent = user.full_name || 'User Profile';
  document.getElementById('display-email').textContent = user.email || '';
}

function setupProfileForm() {
  const form = document.getElementById('profile-form');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const full_name = document.getElementById('profile-full-name').value.trim();
    const phone = document.getElementById('profile-phone').value.trim();
    const password = document.getElementById('profile-password').value;

    try {
      const response = await Utils.fetchWithAuth('/auth/profile', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ full_name, phone, password: password || undefined })
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.message || 'Profile update failed.');

      // Update stored session user object
      const currentUser = Utils.getUser();
      currentUser.full_name = full_name;
      currentUser.phone = phone;
      localStorage.setItem(CONFIG.STORAGE_KEYS.USER, JSON.stringify(currentUser));

      Utils.showAlert('Profile updated successfully!', 'success');
      loadUserProfile();

    } catch (err) {
      Utils.showAlert(err.message);
    }
  });
}
