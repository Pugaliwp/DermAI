# AI-Skin-Health-Screening-Portal 🩺🔬

An AI-powered dermatological screening web application designed for early detection, classification, and clinical risk evaluation of skin lesions and dermatological conditions.

---

## 📁 Repository Directory Structure

```
AI-Skin-Health-Screening-Portal/
│
├── frontend/             # HTML5/CSS3 Glassmorphic UI web portal (Patient & Admin dashboards)
├── backend/              # Node.js Express REST API server (JWT auth, file uploads, PDF reports)
├── ai-service/           # Python FastAPI AI microservice (CNN image inference engine)
├── database/             # Relational SQL database schema and seed data (`skin_portal.sql`)
├── dataset/              # Dermatological image dataset guidelines, structure, and metadata
└── docs/                 # System architecture, API documentation, and setup manuals
```

---

## 🚀 Key Features

1. **AI Image Analysis**: Upload skin lesion images for real-time classification (Melanoma, Eczema, Psoriasis, Basal Cell Carcinoma, etc.) powered by ResNet deep learning.
2. **Clinical Risk Scoring**: Instant risk status badges (High, Moderate, Low) with automated doctor recommendation guidelines.
3. **Medical PDF Reports**: Export high-resolution downloadable diagnostic summary reports generated on demand.
4. **Interactive Disease Encyclopedia**: Comprehensive database of symptoms, prevention protocols, and treatments for common skin conditions.
5. **Secure Authentication & Roles**: JWT-based security model supporting Patient users and Administrator management portals.
6. **Modern UI/UX**: Dark mode glassmorphism user interface designed with responsive micro-animations and micro-interactions.

---

## 🛠 Tech Stack

- **Frontend**: Vanilla HTML5, Custom CSS3 Design System (Glassmorphism), Vanilla JavaScript (ES6+)
- **Backend API**: Node.js, Express.js, JWT (`jsonwebtoken`), Multer, PDFKit, Axios
- **AI Microservice**: Python 3.10+, FastAPI, Uvicorn, Pillow, NumPy, Scikit-Learn
- **Database**: SQLite3 / MySQL 8.0+
- **Documentation**: Markdown, Mermaid Diagrams

---

## 📖 Component Overview

| Directory | Sub-Component | Tech / Language | Key Function |
| :--- | :--- | :--- | :--- |
| `frontend/` | Web Client | HTML5 / CSS3 / JS | Interactive patient & admin web interfaces |
| `backend/` | REST API Server | Node.js / Express | Business logic, authentication, file storage & PDF generator |
| `ai-service/` | AI Engine | Python / FastAPI | Convolutional neural network skin disease classification |
| `database/` | SQL Database | SQL (MySQL/SQLite) | Users, screenings, admin, and disease knowledge schemas |
| `dataset/` | Image Dataset | Metadata / CSV | HAM10000 / ISIC dataset splits and guidelines |
| `docs/` | Project Docs | Markdown | Architecture, API specs, and deployment guides |

---

## ⚙️ Quick Start Guide

### 1. Start AI Microservice (Port 8000)
```bash
cd ai-service
pip install -r requirements.txt
python app.py
```

### 2. Start Backend REST API (Port 5000)
```bash
cd backend
npm install
npm run dev
```

### 3. Launch Frontend Client (Port 3000)
```bash
cd frontend
npx serve . -p 3000
```

Access the application in your browser at `http://localhost:3000`.

---

## 📜 Documentation Links

- [System Architecture & Component Breakdown](docs/ARCHITECTURE.md)
- [Complete REST API Reference](docs/API_DOCUMENTATION.md)
- [Step-by-Step Setup & Installation Guide](docs/SETUP_GUIDE.md)
- [Dataset Guidelines & Structure](dataset/README.md)

---

## ⚠️ Disclaimer

*This portal is designed for preliminary screening support and educational purposes only. It is not a substitute for professional medical advice, diagnosis, or treatment. Always consult a qualified dermatologist for medical concerns.*
