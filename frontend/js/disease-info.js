/* Disease Information Knowledge Base Controller */
document.addEventListener('DOMContentLoaded', async () => {
  await loadDiseaseList();
  
  const urlParams = new URLSearchParams(window.location.search);
  const diseaseParam = urlParams.get('disease');
  if (diseaseParam) {
    highlightDisease(diseaseParam);
  }
});

let diseasesCache = [];

async function loadDiseaseList() {
  // We use the static 7 model classes to ensure perfect alignment with the AI model.
  diseasesCache = getDiseases();
  renderDiseaseCards(diseasesCache);
}

function renderDiseaseCards(diseases) {
  const container = document.getElementById('disease-grid');
  if (!container) return;

  container.innerHTML = diseases.map(item => `
    <div class="feature-card disease-card" id="disease-card-${item.code.toLowerCase()}">
      <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom: 1rem;">
        <div>
          <h3 style="font-size: 1.3rem; color: var(--dark-navy); margin-bottom: 0.25rem;">${item.disease_name}</h3>
          <span style="font-family: monospace; color: var(--slate-500); font-size: 0.85rem; font-weight: 600;">Code: ${item.code}</span>
        </div>
        <span class="badge badge-risk-${item.risk_class}">${item.risk_level}</span>
      </div>
      <p style="color: var(--slate-600); margin-bottom: 1.25rem; font-size: 0.95rem;">${item.description}</p>
      
      <div style="background-color: var(--light-bg); padding: 1rem; border-radius: var(--radius-md); margin-bottom: 1rem;">
        <strong style="color: var(--primary-dark); display:block; font-size: 0.85rem; text-transform: uppercase;">Symptoms:</strong>
        <p style="font-size: 0.9rem; color: var(--slate-700);">${item.symptoms}</p>
      </div>

      <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; font-size: 0.85rem; margin-bottom: 1.5rem;">
        <div>
          <strong style="color: var(--slate-500);">Prevention:</strong>
          <p style="color: var(--slate-700);">${item.prevention}</p>
        </div>
        <div>
          <strong style="color: var(--slate-500);">Treatment:</strong>
          <p style="color: var(--slate-700);">${item.treatment}</p>
        </div>
      </div>
    </div>
  `).join('');
}

function highlightDisease(code) {
  const targetId = `disease-card-${code.toLowerCase()}`;
  const el = document.getElementById(targetId);
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'center' });
    el.style.border = '2px solid var(--primary)';
    el.style.boxShadow = '0 0 25px rgba(2, 132, 199, 0.3)';
  }
}

function getDiseases() {
  return [
    {
      disease_name: "Melanoma",
      code: "MEL",
      description: "A malignant skin tumor arising from melanocytes. Early recognition and professional evaluation are important.",
      symptoms: "A changing or unusual mole, asymmetry, irregular borders, multiple colors, increasing size, or a new suspicious lesion.",
      prevention: "Sun protection, avoiding excessive UV exposure, and regular skin checks.",
      treatment: "Treatment depends on stage and may include surgical removal and specialist-directed therapies.",
      risk_level: "HIGH RISK",
      risk_class: "high"
    },
    {
      disease_name: "Melanocytic Nevus",
      code: "NV",
      description: "A common benign skin lesion formed by melanocytes, commonly known as a mole.",
      symptoms: "Usually a stable, well-defined pigmented spot or raised mole.",
      prevention: "Sun protection and monitoring for changes in existing moles.",
      treatment: "Usually no treatment is required unless the lesion changes or a dermatologist recommends removal.",
      risk_level: "USUALLY BENIGN",
      risk_class: "low"
    },
    {
      disease_name: "Basal Cell Carcinoma",
      code: "BCC",
      description: "A common type of skin cancer originating from basal cells of the epidermis.",
      symptoms: "A pearly or waxy bump, persistent sore, bleeding lesion, or a lesion that does not heal.",
      prevention: "Sun protection, protective clothing, and avoiding excessive UV exposure.",
      treatment: "May include surgical excision, Mohs surgery, or other dermatologist-directed treatments.",
      risk_level: "HIGH RISK",
      risk_class: "high"
    },
    {
      disease_name: "Actinic Keratosis / Intraepithelial Carcinoma",
      code: "AKIEC",
      description: "A sun-related keratotic skin lesion that can represent actinic keratosis or squamous-cell carcinoma in situ/intraepithelial carcinoma.",
      symptoms: "Rough, scaly, crusted, or persistent patches, often on chronically sun-exposed skin.",
      prevention: "Regular sun protection and limiting prolonged UV exposure.",
      treatment: "May include cryotherapy, topical treatments, curettage, or other dermatologist-directed treatment depending on the lesion.",
      risk_level: "MODERATE–HIGH RISK",
      risk_class: "moderate"
    },
    {
      disease_name: "Benign Keratosis",
      code: "BKL",
      description: "A group of benign keratotic skin lesions, including seborrheic keratosis-like lesions.",
      symptoms: "Well-defined rough, scaly, waxy, or pigmented growths.",
      prevention: "No specific prevention is established; monitor lesions for significant changes.",
      treatment: "Usually unnecessary unless the lesion is irritated, symptomatic, or requires diagnostic removal.",
      risk_level: "USUALLY BENIGN",
      risk_class: "low"
    },
    {
      disease_name: "Dermatofibroma",
      code: "DF",
      description: "A common benign fibrous skin lesion.",
      symptoms: "A firm small nodule, commonly occurring on the limbs, that may feel harder than the surrounding skin.",
      prevention: "No specific prevention is established.",
      treatment: "Usually requires no treatment. Removal may be considered if symptomatic or if diagnosis is uncertain.",
      risk_level: "USUALLY BENIGN",
      risk_class: "low"
    },
    {
      disease_name: "Vascular Lesion",
      code: "VASC",
      description: "A skin lesion associated with blood vessels, including common benign vascular growths.",
      symptoms: "May appear as red, purple, or bluish spots, patches, or raised lesions.",
      prevention: "Depends on the specific vascular lesion; general skin protection is appropriate.",
      treatment: "Often no treatment is required, although selected lesions may be treated by a dermatologist using procedures such as laser therapy.",
      risk_level: "USUALLY BENIGN",
      risk_class: "low"
    }
  ];
}
