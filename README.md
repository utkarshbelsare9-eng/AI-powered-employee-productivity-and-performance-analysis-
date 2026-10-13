# AI-Powered Employee Productivity & Performance Analyzer

A production-style, enterprise HR Analytics web application built with **Python Flask, SQLAlchemy, MySQL/SQLite, Bootstrap 5, Chart.js and Scikit-learn**. It tracks employee attendance, tasks and performance, and uses a trained **Machine Learning model (Random Forest)** to predict performance grades, attrition/burnout risk, promotion eligibility, and generate personalized recommendations.

---

## 1. Project Overview

This platform gives Admins, Managers and Employees role-specific dashboards to manage the full employee productivity lifecycle:

- Employee, department and manager management
- Daily attendance tracking (present/absent/leave/WFH/late/overtime)
- Task assignment and progress tracking
- Automatically computed productivity & performance metrics
- An ML model that predicts performance grade (Excellent / Good / Average / Poor), attrition risk, burnout risk and promotion eligibility
- A rule-based recommendation engine for personalized growth suggestions
- Company-wide analytics dashboards (bar / pie / line / radar charts)
- PDF and Excel report export (per-employee and company-wide)
- CSV bulk upload for employee, attendance and task data
- Notifications, leave approval workflow, achievements, skills tracking
- Dark mode, profile settings, secure role-based authentication

---

## 2. Features

### Authentication
Secure login (hashed passwords via Werkzeug), "Remember Me", session expiration, forgot-password flow, role-based access control (Admin / Manager / Employee) enforced with a `@role_required` decorator.

### Admin
Dashboard · Add/Edit/Delete Employee · Department Management · Assign Manager · Upload Employee/Attendance/Task CSV · Generate Reports · View AI Insights/Predictions/Recommendations · View Analytics · Download PDF/Excel · System Settings (user account management)

### Manager
View Team · Assign Tasks · Track Employees · Monitor Attendance · Review Performance · Approve/Reject Leave · View AI Suggestions · Performance Comparison · Monthly Reports

### Employee
Profile · Attendance History · Task History · Performance Score · Monthly Productivity · Recommendations · Achievements · Skill Development Suggestions · Download Own Report

---

## 3. Architecture

```
Browser (Bootstrap 5 + Chart.js + Vanilla JS)
        │
        ▼
Flask App (Blueprints = Controllers)
   ├── routes/        → auth, dashboard, employees, attendance,
   │                    tasks, analytics, prediction, reports,
   │                    admin, profile, api  (JSON endpoints for charts)
   ├── models/         → SQLAlchemy ORM models (Users, Employees,
   │                    Attendance, Tasks, Performance, Predictions...)
   ├── machine_learning/ → train_model.py, predict.py (Random Forest)
   ├── utils/          → shared helpers (scoring, decorators)
   └── templates/      → Jinja2 + Bootstrap 5 views
        │
        ▼
Database (SQLite by default, MySQL-ready via SQLAlchemy URI)
```

The app follows an MVC-style structure: Models (`models/`), Views (`templates/`), Controllers (`routes/` blueprints — see `controllers/__init__.py` for a note on this convention).

---

## 4. Folder Structure

```
EmployeeProductivityAI/
├── frontend/
│   ├── web/
│   │   ├── templates/         # Jinja2 views (dashboard, employee dossiers, analytics, login...)
│   │   ├── static/            # Static assets (css, js, images)
│   │   └── package.json       # Frontend scripts and configuration
│   └── mobile/
│       └── README.md          # Mobile application blueprint & REST API contract
├── backend/
│   ├── app/
│   │   ├── api/               # RESTful API endpoints (/api/v1/) with JWT authentication
│   │   ├── web_routes/        # Web dashboard routes & controllers
│   │   ├── models/            # SQLAlchemy ORM models
│   │   ├── machine_learning/  # Random Forest training and inference
│   │   ├── utils/             # Metric computations, security helpers, decorators
│   │   ├── config.py          # Environment and application configuration
│   │   └── extensions.py      # SQLAlchemy, LoginManager, CSRF, CORS instances
│   ├── tests/                 # Automated test suite (pytest)
│   ├── requirements.txt       # Backend dependencies
│   └── run.py                 # Backend application server entry point
├── database/
│   ├── schema.sql             # MySQL DDL for schema creation
│   └── seed.py                # Realistic sample data seeder
├── ml_artifacts/              # Trained ML model (.joblib), scalers, and metrics.json
├── datasets/                  # ML training dataset (CSV)
├── desktop_agent/             # Cross-platform desktop telemetry collector
├── storage/
│   ├── uploads/               # Employee profile pictures
│   └── reports/               # Generated PDF & Excel employee reports
├── scripts/                   # Database maintenance & account setup scripts
├── docs/                      # Technical documentation & API references
├── .env.example               # Safe environment variable template
├── .gitignore                 # Comprehensive version control ignore rules
├── requirements.txt           # Unified dependency specifications
├── app.py                     # Root execution forwarding script
└── README.md                  # Project overview and documentation
```

---

## 5. Installation

**Requirements:** Python 3.10+

```bash
cd EmployeeProductivityAI
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Run (zero-config, uses SQLite)

```bash
python app.py
```

On first run, the app automatically:
1. Creates all database tables
2. Trains the ML model (if `model/performance_model.joblib` doesn't exist yet)
3. Seeds the database with realistic sample data (if empty)

Then open **http://localhost:5000**

### Demo Login Credentials

| Role     | Username                | Password       |
|----------|--------------------------|----------------|
| Admin    | `admin`                  | `Admin@123`    |
| Manager  | `manager.engineering`    | `Manager@123`  |
| Employee | `emp2` ... `emp46`       | `Employee@123` |

### Switch to MySQL (optional)

1. Create the database: `mysql -u root -p < database/schema.sql` (optional — SQLAlchemy will also create tables automatically)
2. Copy `.env.example` to `.env` and set `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_HOST`, `MYSQL_DB`
3. Re-run `python app.py`

### Re-train the ML model manually

```bash
python machine_learning/train_model.py
```

### Re-seed sample data manually

```bash
python database/seed.py
```

---

## 6. API Documentation (internal JSON endpoints)

Used by the dashboard/analytics pages to render Chart.js visuals (all require login):

| Endpoint | Description |
|---|---|
| `GET /api/charts/department-performance` | Avg performance score per department |
| `GET /api/charts/grade-distribution` | Count of employees per performance grade |
| `GET /api/charts/attendance-trend` | Daily present-count for the last 14 days |
| `GET /api/charts/monthly-trend` | Avg performance score per month |

Report/export endpoints:

| Endpoint | Description |
|---|---|
| `GET /reports/employee/<id>/pdf` | Download a single employee's PDF report |
| `GET /reports/employee/<id>/excel` | Download a single employee's Excel report |
| `GET /reports/company/excel` | Download company-wide Excel report (Admin/Manager) |

---

## 7. Database Schema

See `database/schema.sql` for the full MySQL DDL. Core tables: `departments`, `users`, `employees`, `attendance`, `tasks`, `performance`, `predictions`, `leaves`, `skills`, `achievements`, `notifications` — all normalized with foreign keys (e.g. `employees.department_id → departments.id`, `employees.manager_id → employees.id` self-referential, `attendance.employee_id → employees.id`, etc).

---

## 8. Machine Learning Workflow

1. **Data**: `dataset/employee_performance_dataset.csv` (auto-generated synthetic but realistic dataset of 1200 records if none exists) with 12 input features: attendance %, avg working hours, late entries, leave days, tasks assigned/completed, deadlines missed, overtime hours, customer rating, manager rating, skill score, experience years.
2. **Preprocessing**: missing-value imputation (median), label encoding of the target (`Excellent`/`Good`/`Average`/`Poor`), feature scaling with `StandardScaler`.
3. **Split**: 80/20 train-test split, stratified by class.
4. **Model**: `RandomForestClassifier` (300 trees, balanced class weights).
5. **Validation**: 5-fold cross-validation + held-out test metrics — Accuracy, Precision, Recall, F1 (weighted), Confusion Matrix, full classification report.
6. **Explainability**: Feature importance chart saved to `static/images/feature_importance.png`, confusion matrix chart to `static/images/confusion_matrix.png`.
7. **Persistence**: model, scaler, and label encoder saved via `joblib` to `model/`, auto-loaded by Flask on prediction requests.
8. **Serving**: `machine_learning/predict.py` exposes `predict_employee(features) → {grade, confidence, probabilities, attrition_risk, burnout_risk, promotion_eligible, recommendations}`, combining the ML classification with an explainable rule-based risk/recommendation layer.

Latest training run achieved **~73% test accuracy** / **~69% cross-validated accuracy** on the synthetic dataset — reasonable given intentional class-boundary noise; swap in your real HR dataset (same column names) in `dataset/employee_performance_dataset.csv` and re-run `train_model.py` for production use.

---

## 9. Security

- Passwords hashed with Werkzeug's `generate_password_hash` (salted).
- CSRF protection enabled globally via Flask-WTF.
- SQL injection protected by SQLAlchemy's parameterized queries (no raw SQL string concatenation).
- Role-based route protection via `@role_required(...)` decorator; unauthorized/forbidden requests get styled 401/403 pages.
- Secure session cookies (`HttpOnly`, `SameSite=Lax`), configurable session lifetime.
- File uploads restricted by extension whitelist (`ALLOWED_EXTENSIONS`) and size limit (`MAX_CONTENT_LENGTH`).

---

## 10. Future Scope

Face Recognition Attendance · Voice Assistant · Chatbot · Email/SMS Alerts · Google Calendar / Microsoft Teams / Slack / Jira integrations · Power BI export · Generative-AI natural-language dashboard summaries.

---

## 11. License

This project is provided as a starter/reference implementation for educational and internal business use. Adapt and extend freely for your organization.


### Desktop Activity Agent
The project includes an optional privacy-first `desktop_agent/` collector for aggregate keyboard/mouse activity. See `ACTIVITY_DATA_COLLECTION.md` and `desktop_agent/README.md`.


### Admin / Manager Sign Up
The login page now includes an **Admin / Manager Sign Up** option. Only `admin` and `manager`
roles are offered; employee registration is intentionally excluded. New registrations are
created as **Pending Approval** and must be approved by an existing administrator from the
Admin Panel before the new account can log in. A linked employee profile is also created
automatically for the new account.
