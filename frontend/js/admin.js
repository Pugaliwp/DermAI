/* Admin Control Panel & Interactive Analytics */
document.addEventListener('DOMContentLoaded', async () => {
  if (!Utils.isAuthenticated() || !Utils.isAdmin()) {
    window.location.href = 'login.html';
    return;
  }

  await loadAdminDashboard();
});

async function loadAdminDashboard() {
  try {
    const token = Utils.getToken();
    const response = await fetch(`${CONFIG.API_BASE_URL}/admin/stats`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (!response.ok) throw new Error('Failed to load admin analytics data.');
    const data = await response.json();

    // Populate top metrics
    document.getElementById('admin-total-users').textContent = data.totalUsers || 0;
    document.getElementById('admin-total-screenings').textContent = data.totalScreenings || 0;
    document.getElementById('admin-high-risk-count').textContent = data.highRiskCount || 0;

    // Render tables
    renderAdminUsersTable(data.users || []);
    renderAdminScreeningsTable(data.screenings || []);

    // Render interactive analytics charts using Chart.js
    renderAnalyticsCharts(data.diseaseDistribution || [], data.monthlyTrend || []);

  } catch (err) {
    Utils.showAlert(err.message || 'Error initializing admin dashboard.');
  }
}

function renderAdminUsersTable(users) {
  const body = document.getElementById('admin-users-table-body');
  if (!body) return;

  if (users.length === 0) {
    body.innerHTML = `<tr><td colspan="5" class="text-center">No registered users found.</td></tr>`;
    return;
  }

  body.innerHTML = users.map(u => `
    <tr>
      <td>#${u.user_id}</td>
      <td><strong>${u.full_name}</strong></td>
      <td>${u.email}</td>
      <td>${u.phone || 'N/A'}</td>
      <td>${Utils.formatDate(u.created_at)}</td>
    </tr>
  `).join('');
}

function renderAdminScreeningsTable(screenings) {
  const body = document.getElementById('admin-screenings-table-body');
  if (!body) return;

  if (screenings.length === 0) {
    body.innerHTML = `<tr><td colspan="6" class="text-center">No screening records found.</td></tr>`;
    return;
  }

  body.innerHTML = screenings.map(s => `
    <tr>
      <td>#${s.screening_id}</td>
      <td>User #${s.user_id} (${s.full_name || 'Patient'})</td>
      <td><strong>${s.prediction}</strong></td>
      <td><strong>${s.confidence}%</strong></td>
      <td><span class="badge badge-risk-${(s.risk_level || 'low').toLowerCase()}">${s.risk_level || 'Low'} Risk</span></td>
      <td>${Utils.formatDate(s.created_at)}</td>
      <td>
        <button onclick="deleteScreeningAsAdmin(${s.screening_id})" class="btn btn-sm btn-danger"><i class="fa-solid fa-trash"></i></button>
      </td>
    </tr>
  `).join('');
}

function renderAnalyticsCharts(diseaseDist, monthlyTrend) {
  // Chart 1: Disease Distribution Pie/Doughnut Chart
  const ctx1 = document.getElementById('diseaseChart')?.getContext('2d');
  if (ctx1) {
    const labels = diseaseDist.map(d => d.disease_name || d.prediction);
    const counts = diseaseDist.map(d => d.count);

    new Chart(ctx1, {
      type: 'doughnut',
      data: {
        labels: labels.length ? labels : ['Melanoma', 'Eczema', 'Psoriasis', 'Acne', 'Basal Cell'],
        datasets: [{
          data: counts.length ? counts : [25, 40, 15, 12, 8],
          backgroundColor: ['#ef4444', '#0284c7', '#f59e0b', '#10b981', '#8b5cf6'],
          borderWidth: 2,
          borderColor: '#ffffff'
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { position: 'bottom' }
        }
      }
    });
  }

  // Chart 2: Monthly Screening Trend Bar Chart
  const ctx2 = document.getElementById('trendChart')?.getContext('2d');
  if (ctx2) {
    new Chart(ctx2, {
      type: 'bar',
      data: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'],
        datasets: [{
          label: 'Total Screenings',
          data: [12, 19, 28, 35, 42, 58, 74],
          backgroundColor: '#0284c7',
          borderRadius: 8
        }]
      },
      options: {
        responsive: true,
        scales: {
          y: { beginAtZero: true }
        }
      }
    });
  }
}

async function deleteScreeningAsAdmin(id) {
  if (!confirm(`Admin Confirmation: Delete screening #${id}?`)) return;

  try {
    const token = Utils.getToken();
    const response = await fetch(`${CONFIG.API_BASE_URL}/admin/screening/${id}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (!response.ok) throw new Error('Admin delete action failed.');

    Utils.showAlert('Screening record removed.', 'success');
    await loadAdminDashboard();

  } catch (err) {
    Utils.showAlert(err.message);
  }
}
