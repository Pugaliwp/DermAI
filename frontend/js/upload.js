/* Upload & AI Screening Controller */
document.addEventListener('DOMContentLoaded', () => {
  if (!Utils.isAuthenticated()) {
    window.location.href = 'login.html';
    return;
  }

  setupUploadEvents();
});

let selectedFile = null;

function setupUploadEvents() {
  const dropZone = document.getElementById('upload-dropzone');
  const fileInput = document.getElementById('skin-image-input');
  const previewContainer = document.getElementById('preview-container');
  const imagePreview = document.getElementById('image-preview');
  const analyzeBtn = document.getElementById('analyze-btn');
  const cancelBtn = document.getElementById('cancel-preview-btn');

  if (!dropZone || !fileInput) return;

  // Trigger input on click
  dropZone.addEventListener('click', () => fileInput.click());

  // Drag & drop handlers
  ['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropZone.classList.add('dragover');
    }, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropZone.classList.remove('dragover');
    }, false);
  });

  dropZone.addEventListener('drop', (e) => {
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelection(files[0]);
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      handleFileSelection(e.target.files[0]);
    }
  });

  cancelBtn?.addEventListener('click', () => {
    selectedFile = null;
    fileInput.value = '';
    previewContainer.style.display = 'none';
    dropZone.style.display = 'block';
  });

  analyzeBtn?.addEventListener('click', () => {
    if (!selectedFile) {
      Utils.showAlert('Please select an image first.');
      return;
    }
    submitScreeningImage(selectedFile);
  });
}

function handleFileSelection(file) {
  // Validate File Type
  const validTypes = ['image/jpeg', 'image/jpg', 'image/png'];
  if (!validTypes.includes(file.type.toLowerCase())) {
    Utils.showAlert('Invalid file type. Please upload a JPG, JPEG, or PNG image.');
    return;
  }

  // Validate File Size (Max 5MB)
  const maxSizeInBytes = 5 * 1024 * 1024;
  if (file.size > maxSizeInBytes) {
    Utils.showAlert('File size exceeds maximum limit of 5MB.');
    return;
  }

  selectedFile = file;

  // Show Image Preview
  const reader = new FileReader();
  reader.onload = (e) => {
    const imagePreview = document.getElementById('image-preview');
    const previewContainer = document.getElementById('preview-container');
    const dropZone = document.getElementById('upload-dropzone');

    imagePreview.src = e.target.result;
    dropZone.style.display = 'none';
    previewContainer.style.display = 'block';
  };
  reader.readAsDataURL(file);
}

async function submitScreeningImage(file) {
  const scanOverlay = document.getElementById('scan-overlay');
  const scanStatusText = document.getElementById('scan-status-text');
  
  // Show Scan Loading Screen
  scanOverlay.style.display = 'flex';
  scanStatusText.textContent = 'Preprocessing skin lesion telemetry...';

  setTimeout(() => {
    scanStatusText.textContent = 'Extracting ABCDE features & neural classification...';
  }, 1200);

  const formData = new FormData();
  formData.append('image', file);

  try {
    const token = Utils.getToken();
    const response = await fetch(`${CONFIG.API_BASE_URL}/screening/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.message || 'AI Screening process failed.');
    }

    // Save result to session storage for instant preview
    localStorage.setItem(CONFIG.STORAGE_KEYS.LAST_RESULT, JSON.stringify(data.screening));

    setTimeout(() => {
      scanOverlay.style.display = 'none';
      window.location.href = `result.html?id=${data.screening.screening_id}`;
    }, 2000);

  } catch (err) {
    scanOverlay.style.display = 'none';
    Utils.showAlert(err.message || 'Error executing AI screening.');
  }
}
