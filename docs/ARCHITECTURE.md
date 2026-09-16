# AI Skin Health Screening Portal - System Architecture

This document describes the end-to-end software architecture for the **AI Skin Health Screening Portal**.

## High-Level System Architecture

```
                                  +-----------------------------+
                                  |     Client Web Browser      |
                                  | (HTML5/CSS3 Glassmorphism JS)|
                                  +--------------+--------------+
                                                 |
                                         HTTP / REST APIs
                                                 v
                                  +-----------------------------+
                                  |    Node.js Express Backend  |
                                  |       (Port 5000)           |
                                  +-------+--------------+------+
                                          |              |
                       Auth / CRUD / Logs |              | Multipart Image Forwarding
                                          v              v
                        +-------------------+   +-------------------------+
                        |  Database (MySQL  |   | Python FastAPI AI Service|
                        |   / SQLite3)      |   |       (Port 8000)       |
                        +-------------------+   +-------------------------+
                                                         |
                                                         v
                                                +-----------------+
                                                | CNN Model Engine|
                                                | (ResNet50 / ML) |
                                                +-----------------+
```

## System Components Breakdown

### 1. Frontend (`/frontend`)
- **Role**: Client interface for users and medical administrators.
- **Technologies**: Vanilla HTML5, Modern CSS3 with dark mode glassmorphism UI tokens, Vanilla JavaScript (ES6+ fetch API).
- **Key Modules**:
  - `index.html`: Landing page, portal features, quick assessment CTA.
  - `login.html` & `register.html`: Authentication portals with JWT token storage.
  - `upload.html`: Image dropzone & file validation for skin lesion screening.
  - `result.html`: Detailed screening diagnosis view with confidence score, risk badge, recommendations, and PDF report download.
  - `history.html`: User screening history timeline.
  - `disease-info.html`: Medical knowledge base on skin conditions.
  - `admin.html`: Administrator dashboard for user management and system metrics.

### 2. Backend API (`/backend`)
- **Role**: Core business logic, authentication, file storage, data persistence, and orchestration.
- **Technologies**: Node.js, Express.js, JWT (`jsonwebtoken`), `bcryptjs`, `multer`, `pdfkit`, `sqlite3`/`mysql2`.
- **Key Services**:
  - Auth Controller: User registration, login, JWT issuance, profile updates.
  - Screening Controller: Handles image upload, dispatches image to AI Microservice via Axios, formats diagnostic advice, generates PDF medical reports.
  - Admin Controller: System stats, aggregate reports, disease database management.

### 3. AI Service (`/ai-service`)
- **Role**: Deep Learning inference microservice for automated dermatological screening.
- **Technologies**: Python 3.10+, FastAPI, Uvicorn, Pillow, Scikit-learn, NumPy.
- **Endpoints**:
  - `GET /health`: Service health check and model metadata.
  - `POST /predict`: Accepts binary image uploads and outputs predicted disease label, confidence percentage, risk assessment, and clinical recommendations.

### 4. Database (`/database`)
- **Role**: Relational database storage for users, administrative credentials, screening history, and disease knowledge base.
- **Schema**:
  - `users`: User profiles and hashed credentials.
  - `admin`: Superuser admin credentials.
  - `screenings`: Individual screening records with diagnostic predictions, confidence scores, and recommendations.
  - `diseases`: Knowledge base table for medical condition descriptions, symptoms, prevention, and treatment protocols.

### 5. Datasets (`/dataset`)
- Data storage and preparation directory for raw and preprocessed dermatological datasets (HAM10000 / ISIC Archive).

### 6. Documentation (`/docs`)
- Technical specifications, setup guides, API reference manuals, and architectural diagrams.
