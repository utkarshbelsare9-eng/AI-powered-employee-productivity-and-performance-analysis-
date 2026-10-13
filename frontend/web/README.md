# Web Frontend — Employee Productivity & Performance AI

This folder contains the complete user interface for the web application.

## Directory Structure
- `templates/`: Jinja2 templates (dashboard, employee dossiers, analytics charts, login, tasks, etc.)
- `static/css/`: Corporate glassmorphism theme (`style.css`)
- `static/js/`: Chart.js visualization logic and interactivity (`main.js`)
- `static/images/`: Confusion matrix, feature importance visual charts, and default avatars
- `static/uploads/`: Employee profile avatars

## Communication Layer
The web interface communicates with the Flask server through:
- Direct template rendering for primary MVC views
- JSON API endpoints under `/api/v1/` for dynamic Chart.js charts and live activity telemetry

## Future Migration Roadmap
To transition to a standalone Single Page Application (e.g. Next.js, React, or Vue), the entire business logic and database access have already been abstracted into `/api/v1/` REST endpoints.
