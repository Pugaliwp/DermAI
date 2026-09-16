# AI Skin Health Screening Portal - Setup & Installation Guide

Follow this step-by-step guide to set up and run the entire **AI Skin Health Screening Portal** stack locally.

---

## Prerequisites

- **Node.js**: v18.0.0 or higher
- **Python**: v3.10 or higher
- **pip**: Latest version
- **Git**: For version control
- **Database**: SQLite3 (default built-in) or MySQL 8.0+

---

## 1. Database Setup

### Using SQLite3 (Default Zero-Config Setup)
The backend is configured to automatically initialize SQLite3 using `backend/skin_portal.sqlite`.

### Using MySQL Database (Optional Production Setup)
1. Open your MySQL client or terminal.
2. Run the SQL schema script provided in `database/skin_portal.sql`:
   ```bash
   mysql -u root -p < database/skin_portal.sql
   ```

---

## 2. AI Microservice Setup (Python FastAPI)

1. Navigate to the `ai-service` directory:
   ```bash
   cd ai-service
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # On Windows PowerShell:
   .\venv\Scripts\Activate.ps1
   # On Linux/macOS:
   source venv/bin/activate
   ```
3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the AI service engine:
   ```bash
   python app.py
   # Or using uvicorn directly:
   uvicorn app:app --host 0.0.0.0 --port 8000 --reload
   ```
5. Verify AI service health:
   Open browser at `http://localhost:8000/health`.

---

## 3. Backend REST API Setup (Node.js Express)

1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```
2. Install npm package dependencies:
   ```bash
   npm install
   ```
3. Start the Express server:
   ```bash
   npm run dev
   # Or:
   npm start
   ```
4. Verify backend server status:
   Server will log `[DermAI Backend] Running on http://localhost:5000`.

---

## 4. Frontend Setup (HTML5/CSS3/JS Web Client)

1. Navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```
2. Serve static frontend files using any HTTP static server, e.g., Live Server or `npx serve`:
   ```bash
   npx serve . -p 3000
   ```
3. Open browser at `http://localhost:3000` (or double click `frontend/index.html`).

---

## Testing Default Accounts

- **Default User**: `jane@example.com` | Password: `admin123`
- **Default Admin**: `admin` | Password: `admin123`
