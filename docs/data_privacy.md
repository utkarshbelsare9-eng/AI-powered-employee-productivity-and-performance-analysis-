# Data Privacy & Ethical Telemetry Policy

## 1. Principles
The **Desktop Activity Tracker** and workstation monitoring module (`desktop_agent/`) are architected on the principle of **privacy by design**.

## 2. What Is Collected
- `keyboard_events`: Aggregate count of keystroke events in a 60-second window.
- `mouse_moves`: Aggregate number of cursor movement events.
- `mouse_clicks`: Aggregate count of clicks.
- `scroll_events`: Number of scroll operations.
- `idle_seconds`: Inactivity duration within the 60-second slice.
- `active_application`: The active process/application binary name (e.g. `code.exe`, `chrome.exe`).

## 3. What Is NEVER Collected
- **No Keystroke Logging**: The agent does NOT record actual keys pressed, typed letters, or passwords.
- **No Content Capture**: No document contents, clipboard items, or typed messages are accessed.
- **No Visual Surveillance**: No screenshots, webcam streams, or screen recordings.
- **No Document Titles**: Window titles containing sensitive document names are excluded.

## 4. Transmission Security
- Agent pings require per-employee HMAC authentication tokens generated in the settings console.
- Data is transmitted over HTTPS/TLS to `/api/v1/activity/agent/ping`.
