# Mobile Application Blueprint (Android & iOS)

This directory is reserved for the future native / hybrid mobile application (React Native + Expo recommended).

## Backend Integration Details
The backend now provides full mobile-ready RESTful JSON API endpoints under `/api/v1/`:

| Module | Endpoint | Method | Description |
| :--- | :--- | :--- | :--- |
| **Auth** | `/api/v1/auth/login` | `POST` | Exchange username & password for a signed Bearer JWT token |
| **Auth** | `/api/v1/auth/forgot-password`| `POST` | Request 6-digit OTP dispatched to Admin (`utkarshbelsare9@gmail.com`) |
| **Auth** | `/api/v1/auth/reset-password` | `POST` | Submit OTP and new password |
| **Auth** | `/api/v1/auth/me` | `GET` | Retrieve authenticated profile |
| **Attendance** | `/api/v1/attendance/check-in` | `POST` | Employee mobile check-in |
| **Attendance** | `/api/v1/attendance/check-out` | `POST` | Employee mobile check-out |
| **Attendance** | `/api/v1/attendance/history` | `GET` | List recent attendance records |
| **Tasks** | `/api/v1/tasks` | `GET` | List assigned tasks |
| **Tasks** | `/api/v1/tasks/<id>/status` | `PATCH`| Update task status (e.g. Completed) |
| **Predictions** | `/api/v1/predictions/employee/<id>` | `GET` | Run live Random Forest inference |
| **Analytics** | `/api/v1/analytics/dashboard` | `GET` | Dashboard KPI summary figures |
| **Leaves** | `/api/v1/leaves` | `GET/POST`| Apply and view leave requests |

## Recommended Mobile Stack
- **Framework:** React Native / Expo SDK 51+
- **Navigation:** Expo Router / React Navigation
- **State Management:** Zustand or React Query
- **Secure Storage:** `expo-secure-store` for JWT persistence
- **HTTP Client:** Axios with Authorization Bearer interceptors
