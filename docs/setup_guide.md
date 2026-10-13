# Setup & Deployment Guide

## 1. Quick Start

### Step 1: Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### Step 2: Start Unified Backend & Web Server
From the `backend/` directory:
```bash
python run.py
```
Or from the project root:
```bash
python app.py
```

- **Web Dashboard:** [http://localhost:5000](http://localhost:5000)
- **RESTful API:** [http://localhost:5000/api/v1](http://localhost:5000/api/v1)

---

## 2. Default Login Credentials

| Role | Username | Password | Email |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `Admin@123` | `admin@company.com` |
| **Manager** | `manager` | `Manager@123` | `manager@company.com` |
| **Employee** | `emp1` | `Employee@123` | `emp1@company.com` |

---

## 3. Running Automated Tests
```bash
python backend/tests/test_api.py
```

## 4. Re-training the AI Model
```bash
python backend/app/machine_learning/train_model.py
```
Outputs are serialized to `ml_artifacts/`.
