# AI Skin Health Screening Portal - API Documentation

This reference guide details all REST API endpoints exposed by the Node.js Express Backend and the Python FastAPI AI Microservice.

---

## 1. Node.js Express Backend API (Port 5000)

Base URL: `http://localhost:5000/api`

### Authentication Endpoints

#### `POST /auth/register`
Registers a new user account.
- **Request Body**:
  ```json
  {
    "full_name": "Jane Doe",
    "email": "jane@example.com",
    "phone": "+15550192",
    "password": "securepassword123"
  }
  ```
- **Response (201 Created)**:
  ```json
  {
    "message": "User registered successfully",
    "token": "<JWT_TOKEN>",
    "user": { "user_id": 1, "full_name": "Jane Doe", "email": "jane@example.com" }
  }
  ```

#### `POST /auth/login`
Authenticates existing users or administrators.
- **Request Body**:
  ```json
  {
    "email": "jane@example.com",
    "password": "securepassword123",
    "role": "user"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "message": "Login successful",
    "token": "<JWT_TOKEN>",
    "user": { "user_id": 1, "full_name": "Jane Doe", "email": "jane@example.com" }
  }
  ```

---

### Screening Endpoints

#### `POST /screening/upload`
Uploads a skin lesion image and initiates AI screening prediction.
- **Headers**: `Authorization: Bearer <JWT_TOKEN>`
- **Content-Type**: `multipart/form-data`
- **Form Data**:
  - `image`: File (JPEG, PNG, WebP)
- **Response (200 OK)**:
  ```json
  {
    "screening_id": 101,
    "prediction": "Melanoma",
    "confidence": 96.50,
    "risk_level": "High",
    "recommendation": "Consult a dermatologist immediately for formal evaluation.",
    "image_path": "uploads/1723368291-skin.jpg",
    "created_at": "2026-08-11T13:57:31.000Z"
  }
  ```

#### `GET /screening/history`
Retrieves screening records for the authenticated user.
- **Headers**: `Authorization: Bearer <JWT_TOKEN>`
- **Response (200 OK)**: Array of screening objects.

#### `GET /screening/download-pdf/:screening_id`
Generates and downloads a clinical PDF diagnostic summary report.
- **Headers**: `Authorization: Bearer <JWT_TOKEN>`
- **Response**: Binary PDF file (`application/pdf`).

---

### Disease Information Endpoints

#### `GET /diseases`
Retrieves the comprehensive list of skin diseases and medical guidance.
- **Response (200 OK)**: Array of disease knowledge objects.

---

## 2. Python FastAPI AI Service API (Port 8000)

Base URL: `http://localhost:8000`

### `GET /health`
Performs health check and returns AI model configuration status.
- **Response (200 OK)**:
  ```json
  {
    "status": "online",
    "service": "DermAI Python AI Service",
    "model_version": "1.0.0-resnet50"
  }
  ```

### `POST /predict`
Direct AI lesion image prediction service endpoint.
- **Content-Type**: `multipart/form-data`
- **Form Data**:
  - `image`: File binary
- **Response (200 OK)**:
  ```json
  {
    "prediction": "Melanoma",
    "confidence": 96.50,
    "risk_level": "High",
    "recommendation": "Consult a dermatologist immediately for formal histological evaluation.",
    "probabilities": {
      "Melanoma": 96.50,
      "Actinic Keratosis": 2.10,
      "Basal Cell Carcinoma": 1.40
    }
  }
  ```
