/* Screening History Controller */
document.addEventListener('DOMContentLoaded', async () => {
  if (!Utils.isAuthenticated()) {
    window.location.href = 'login.html';
    return;
  }

  await loadScreeningHistory();
  setupFilters();
});

let allHistoryItems = [];

async function loadScreeningHistory() {
  try {
    const response = await Utils.fetchWithAuth('/screening/user-screenings');

    if (!response.ok) throw new Error('Failed to load history');
    allHistoryItems = await response.json();
    renderHistoryTable(allHistoryItems);

  } catch (err) {
    const container = document.getElementById('history-table-body');
    if (container) {
      container.innerHTML = `<tr><td colspan="7" class="text-center" style="padding: 2.5rem; color: #ef4444;">Failed to load records. ${err.message}</td></tr>`;
    }
    if (err.message !== 'Session expired') {
      Utils.showAlert(err.message);
    }
  }
}

function renderHistoryTable(items) {
  const container = document.getElementById('history-table-body');
  if (!container) return;

  if (items.length === 0) {
    container.innerHTML = `<tr><td colspan="6" class="text-center" style="padding: 2.5rem; color: var(--slate-400);">No screening history records found.</td></tr>`;
    return;
  }

  container.innerHTML = items.map(item => `
    <tr>
      <td>#${item.screening_id}</td>
      <td>
        <img src="${item.image_path.startsWith('http') ? item.image_path : CONFIG.API_BASE_URL.replace('/api', '') + '/' + item.image_path}" 
             style="width: 54px; height: 54px; border-radius: 10px; object-fit: cover; border: 1px solid var(--slate-200);" alt="Skin Scan"/>
      </td>
      <td><strong style="color: var(--dark-navy); font-size: 1rem;">${item.prediction}</strong></td>
      <td><strong>${Utils.formatConfidence(item.confidence)}</strong></td>
      <td><span class="badge badge-risk-${(item.risk_level || 'low').toLowerCase()}">${item.risk_level || 'Low'} Risk</span></td>
      <td>${Utils.formatDate(item.created_at)}</td>
      <td>
        <div style="display:flex; gap: 0.5rem;">
          <a href="result.html?id=${item.screening_id}" class="btn btn-sm btn-outline"><i class="fa-solid fa-eye"></i> Details</a>
          <button onclick="deleteScreeningRecord(${item.screening_id})" class="btn btn-sm btn-danger"><i class="fa-solid fa-trash"></i></button>
        </div>
      </td>
    </tr>
  `).join('');
}

function setupFilters() {
  const searchInput = document.getElementById('history-search');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      const q = e.target.value.toLowerCase();
      const filtered = allHistoryItems.filter(item => 
        item.prediction.toLowerCase().includes(q) || 
        (item.risk_level && item.risk_level.toLowerCase().includes(q))
      );
      renderHistoryTable(filtered);
    });
  }
}

async function deleteScreeningRecord(id) {
  if (!confirm('Are you sure you want to delete this screening record?')) return;

  try {
    const response = await Utils.fetchWithAuth(`/screening/${id}`, {
      method: 'DELETE'
    });

    if (!response.ok) throw new Error('Failed to delete record.');
    
    Utils.showAlert('Record deleted successfully.', 'success');
    allHistoryItems = allHistoryItems.filter(item => item.screening_id !== id);
    renderHistoryTable(allHistoryItems);

  } catch (err) {
    Utils.showAlert(err.message);
  }
}
