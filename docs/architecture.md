# Architecture & System Design Document

**Project:** AI-Powered Employee Productivity & Performance Analyzer  
**Architecture Style:** Decoupled Modular Monolith / Dual-Channel (SSR Web + RESTful Mobile API)

---

## 1. High-Level Architecture Overview

The system is organized into decoupled layers:

1. **Frontend Layer**:
   - `frontend/web/`: Jinja2 templates, Bootstrap 5 corporate glassmorphism styling, and Chart.js dashboards.
   - `frontend/mobile/`: Architecture and integration blueprint ready for React Native / Expo native iOS and Android apps.

2. **Backend Application Layer (`backend/app/`)**:
   - **Application Factory**: Centralized in `app/__init__.py`.
   - **Configuration**: `app/config.py` loading `.env` securely.
   - **Extensions**: Centralized in `app/extensions.py` (`db`, `login_manager`, `csrf`, `cors`).
   - **Mobile REST API (`app/api/`)**: Mounted at `/api/v1/`, secured with Bearer JWT tokens.
   - **Web Controllers (`app/web_routes/`)**: Mounted for web views and session authentication.
   - **Data Models (`app/models/`)**: Normalized relational models with foreign-key constraints.
   - **Machine Learning (`app/machine_learning/`)**: Inference and training pipelines loading models from `ml_artifacts/`.
   - **Shared Utilities (`app/utils/`)**: Scoring formulas, Google SMTP mailer, decorators.

3. **Data & Artifact Layers**:
   - `database/`: Embedded SQLite storage (`app.db`) and MySQL schema (`schema.sql`).
   - `ml_artifacts/`: Serialized Random Forest model, scaler, label encoder, and evaluation metrics.
   - `datasets/`: Synthetic 1,200-sample HR dataset for re-training.
   - `storage/`: Persistent document storage (`uploads/` and `reports/`).
   - `desktop_agent/`: Standalone background activity event aggregator.

---

## 2. Authentication Architecture

- **Web Browser Clients**: Session-cookie authentication with Werkzeug password hashing and `Flask-WTF` CSRF protection.
- **Mobile & External Clients**: Stateless **Bearer JWT** tokens generated on `/api/v1/auth/login` and verified via `@jwt_required`.
- **Role-Based Access Control**:
  - `admin`: Global visibility, user approval, department configuration.
  - `manager`: Team supervision, task assignment, leave approvals.
  - `employee`: Personal dashboard, daily check-in/out, self-service tasks and predictions.
