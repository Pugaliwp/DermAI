/* Screening Result & PDF Download Controller */
document.addEventListener('DOMContentLoaded', async () => {
  if (!Utils.isAuthenticated()) {
    window.location.href = 'login.html';
    return;
  }

  const urlParams = new URLSearchParams(window.location.search);
  const screeningId = urlParams.get('id');

  if (screeningId) {
    await fetchScreeningDetail(screeningId);
  } else {
    // Try to load cached last result
    const cached = localStorage.getItem(CONFIG.STORAGE_KEYS.LAST_RESULT);
    if (cached) {
      renderResult(JSON.parse(cached));
    } else {
      window.location.href = 'dashboard.html';
    }
  }

  setupPDFDownload(screeningId);
});

async function fetchScreeningDetail(id) {
  try {
    const response = await Utils.fetchWithAuth(`/screening/${id}`);

    if (!response.ok) throw new Error('Could not fetch screening result');
    const result = await response.json();
    renderResult(result);

  } catch (err) {
    Utils.showAlert(err.message);
  }
}

function formatConfidence(val) {
  if (val == null) return "0.00";
  let num = parseFloat(val);
  if (isNaN(num)) return "0.00";
  if (num <= 1.0) {
    num = num * 100;
  }
  return num.toFixed(2);
}

function renderResult(data) {
  if (!data) return;

  const imageSrc = data.image_path.startsWith('http') || data.image_path.startsWith('data:') 
    ? data.image_path 
    : `${CONFIG.API_BASE_URL.replace('/api', '')}/${data.image_path}`;

  document.getElementById('result-image').src = imageSrc;
  document.getElementById('result-disease-name').textContent = data.prediction || 'Unknown Condition';
  
  const formattedConf = formatConfidence(data.confidence);
  document.getElementById('result-confidence-text').textContent = `${formattedConf}%`;
  
  const fillBar = document.getElementById('result-confidence-fill');
  if (fillBar) {
    fillBar.style.width = `${formattedConf}%`;
  }
  
  const modelNameElem = document.getElementById('result-model-name');
  if (modelNameElem) {
    modelNameElem.textContent = data.model_name || 'Standard';
  }

  const probSection = document.getElementById('probability-section');
  const probBars = document.getElementById('probability-bars');
  
  if (probSection && probBars) {
    probBars.innerHTML = '';
    let probsObj = null;
    
    try {
      probsObj = typeof data.probabilities === 'string' ? JSON.parse(data.probabilities) : data.probabilities;
    } catch(e) {
      console.warn("Failed to parse probabilities", e);
    }

    if (probsObj && Object.keys(probsObj).length > 0) {
      probSection.style.display = 'block';
      
      const orderedClasses = ['MEL', 'NV', 'BCC', 'AKIEC', 'BKL', 'DF', 'VASC'];
      const predictedClass = data.class_code;

      orderedClasses.forEach(cls => {
        if (probsObj[cls] !== undefined) {
          const val = probsObj[cls];
          const pct = formatConfidence(val);
          const isPredicted = (cls === predictedClass) || (data.prediction && data.prediction.toUpperCase().includes(cls));
          
          const barColor = isPredicted ? 'linear-gradient(90deg, var(--primary) 0%, var(--accent) 100%)' : 'var(--slate-400)';
          const textColor = isPredicted ? 'var(--primary)' : 'var(--slate-600)';
          const fontWeight = isPredicted ? '700' : '500';

          const html = `
            <div class="confidence-bar-container" style="margin: 0;">
              <div class="confidence-header" style="font-size: 0.8rem; font-weight: ${fontWeight}; margin-bottom: 0.2rem;">
                <span style="color: ${textColor};">${cls}</span>
                <span style="color: ${textColor};">${pct}%</span>
              </div>
              <div class="confidence-bar" style="height: 6px; background-color: var(--slate-200);">
                <div class="confidence-fill" style="width: ${pct}%; background: ${barColor}; height: 100%; border-radius: 50px;"></div>
              </div>
            </div>
          `;
          probBars.insertAdjacentHTML('beforeend', html);
        }
      });
    } else {
      probSection.style.display = 'none';
    }
  }

  const riskLevel = data.risk_level || 'Low';
  const riskBadge = document.getElementById('result-risk-badge');
  riskBadge.textContent = `${riskLevel} Risk`;
  riskBadge.className = `badge badge-risk-${riskLevel.toLowerCase()}`;

  document.getElementById('result-recommendation').textContent = data.recommendation || 'Consult a dermatologist for a professional clinical check.';
  document.getElementById('result-date').textContent = Utils.formatDate(data.created_at || new Date());

  // Link to Disease Info Catalog
  const infoLink = document.getElementById('view-disease-info-link');
  if (infoLink) {
    infoLink.href = `disease-info.html?disease=${encodeURIComponent(data.prediction)}`;
  }
}

function setupPDFDownload(screeningId) {
  const downloadBtn = document.getElementById('download-pdf-btn');
  if (!downloadBtn) return;

  downloadBtn.addEventListener('click', async () => {
    try {
      const token = Utils.getToken();
      const user = Utils.getUser();
      const currentId = screeningId || (JSON.parse(localStorage.getItem(CONFIG.STORAGE_KEYS.LAST_RESULT) || '{}')).screening_id;

      if (!currentId) {
        Utils.showAlert('Screening record ID missing for report generation.');
        return;
      }

      downloadBtn.disabled = true;
      downloadBtn.textContent = 'Generating PDF...';

      const response = await Utils.fetchWithAuth(`/screening/report/${currentId}`);

      if (!response.ok) throw new Error('PDF Generation failed.');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `Skin_Health_Report_${currentId}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();

      Utils.showAlert('PDF Report downloaded successfully!', 'success');
    } catch (err) {
      Utils.showAlert(err.message || 'Could not download report PDF.');
    } finally {
      downloadBtn.disabled = false;
      downloadBtn.innerHTML = `<i class="fa-solid fa-file-pdf"></i> Download PDF Report`;
    }
  });
}
