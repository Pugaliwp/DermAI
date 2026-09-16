/* User Dashboard Script */
document.addEventListener('DOMContentLoaded', async () => {
  if (!Utils.isAuthenticated()) {
    window.location.href = 'login.html';
    return;
  }

  const user = Utils.getUser();
  document.getElementById('user-welcome-name').textContent = user.full_name || 'User';

  loadDashboardData();
});

async function loadDashboardData() {
  try {
    const token = Utils.getToken();
    const res = await fetch(`${CONFIG.API_BASE_URL}/screening/user-screenings`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (!res.ok) throw new Error('Failed to load dashboard data');
    const screenings = await res.json();

    // Render metrics
    document.getElementById('total-screenings-count').textContent = screenings.length;
    
    if (screenings.length > 0) {
      const recent = screenings[0];
      document.getElementById('recent-disease-name').textContent = recent.prediction;
      document.getElementById('recent-confidence').textContent = `${recent.confidence}%`;
      document.getElementById('recent-date').textContent = Utils.formatDate(recent.created_at);
      
      const riskBadge = document.getElementById('recent-risk-badge');
      riskBadge.textContent = recent.risk_level || 'Evaluated';
      riskBadge.className = `badge badge-risk-${(recent.risk_level || 'low').toLowerCase()}`;
    } else {
      document.getElementById('recent-disease-name').textContent = 'No Screenings Yet';
      document.getElementById('recent-confidence').textContent = '--';
      document.getElementById('recent-date').textContent = 'N/A';
    }

    // Populate recent screenings table
    const tableBody = document.getElementById('recent-screenings-list');
    if (tableBody) {
      if (screenings.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="5" class="text-center" style="padding: 2rem; color: var(--slate-400);">No screening history found. Upload an image to start!</td></tr>`;
        return;
      }

      tableBody.innerHTML = screenings.slice(0, 5).map(item => `
        <tr>
          <td>
            <div style="display:flex; align-items:center; gap: 0.75rem;">
              <img src="${item.image_path.startsWith('http') ? item.image_path : CONFIG.API_BASE_URL.replace('/api', '') + '/' + item.image_path}" 
                   style="width: 48px; height: 48px; border-radius: 8px; object-fit: cover;" alt="Skin Sample"/>
              <strong style="color: var(--dark-navy);">${item.prediction}</strong>
            </div>
          </td>
          <td>
            <span class="badge badge-risk-${(item.risk_level || 'low').toLowerCase()}">
              ${item.risk_level || 'Low'}
            </span>
          </td>
          <td><strong>${item.confidence}%</strong></td>
          <td>${Utils.formatDate(item.created_at)}</td>
          <td>
            <button onclick="viewResultDetail(${item.screening_id})" class="btn btn-sm btn-outline">View Result</button>
          </td>
        </tr>
      `).join('');
    }

  } catch (err) {
    console.error('Error loading dashboard:', err);
  }
}

function viewResultDetail(screeningId) {
  window.location.href = `result.html?id=${screeningId}`;
}
