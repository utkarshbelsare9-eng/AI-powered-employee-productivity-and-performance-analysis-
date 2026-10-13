# RESTful API Documentation (`/api/v1`)

All endpoints accept and return `application/json`.
Protected endpoints require:
```http
Authorization: Bearer <your_jwt_token>
```

---

## 1. Authentication Endpoints

### 1.1 Login (Mobile / External Clients)
* **URL:** `POST /api/v1/auth/login`
* **Request:**
  ```json
  {
    "username": "admin",
    "password": "Admin@123"
  }
  ```
* **Response (200 OK):**
  ```json
  {
    "success": true,
    "token": "eyJhbGciOiJIUzI1NiIsIn...",
    "user": {
      "id": 1,
      "username": "admin",
      "email": "admin@company.com",
      "role": "admin"
    }
  }
  ```

### 1.2 Forgot Password Request
* **URL:** `POST /api/v1/auth/forgot-password`
* **Request:** `{"identity": "emp1"}`
* **Response (200 OK):**
  ```json
  {
    "success": true,
    "message": "A 6-digit verification code has been dispatched directly to the Admin..."
  }
  ```

---

## 2. Workforce Management

### 2.1 List Employees
* **URL:** `GET /api/v1/employees?page=1&per_page=20`
* **Headers:** `Authorization: Bearer <token>`
* **Response (200 OK):**
  ```json
  {
    "success": true,
    "total": 45,
    "page": 1,
    "employees": [...]
  }
  ```

---

## 3. Attendance Workflow

### 3.1 Mobile Check-In
* **URL:** `POST /api/v1/attendance/check-in`
* **Headers:** `Authorization: Bearer <token>`
* **Response (200 OK):**
  ```json
  {
    "success": true,
    "message": "Checked in successfully",
    "check_in": "09:30:00"
  }
  ```

### 3.2 Mobile Check-Out
* **URL:** `POST /api/v1/attendance/check-out`
* **Headers:** `Authorization: Bearer <token>`
* **Response (200 OK):**
  ```json
  {
    "success": true,
    "message": "Checked out successfully",
    "check_out": "18:00:00",
    "working_hours": 8.5
  }
  ```

---

## 4. Machine Learning & Predictive Analytics

### 4.1 Run Inference
* **URL:** `GET /api/v1/predictions/employee/<id>`
* **Headers:** `Authorization: Bearer <token>`
* **Response (200 OK):**
  ```json
  {
    "success": true,
    "prediction": {
      "predicted_grade": "Good",
      "confidence": 61.1,
      "burnout_risk": "Low",
      "attrition_risk": "Low",
      "promotion_eligible": true,
      "recommendations": [...]
    }
  }
  ```
