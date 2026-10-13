# Employee ProductivityAI — Desktop Activity Agent

This optional Windows/macOS/Linux helper collects **aggregate activity metrics** outside the browser and sends them to the Flask application every 60 seconds.

Collected:
- keyboard press count (NOT the keys or typed text)
- mouse movement count
- mouse click count
- scroll event count
- idle seconds
- active application/process name only (no window title, document name, clipboard or screenshots)

The agent needs a per-employee activity token generated from **Settings → Desktop Activity Tracker**.

## Install

From the `EmployeeProductivityAI` directory:

```bash
pip install -r requirements.txt
```

## Configure

Set:

```bash
PRODUCTIVITY_AI_SERVER=http://127.0.0.1:5000
PRODUCTIVITY_AI_AGENT_TOKEN=<token from the web UI>
```

Then run:

```bash
python desktop_agent/agent.py
```

The collector is intentionally transparent and should only be deployed with employee notice/consent and according to applicable workplace/privacy requirements.
