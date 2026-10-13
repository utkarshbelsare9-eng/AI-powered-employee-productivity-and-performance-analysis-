"""
AI-Powered Employee Productivity & Performance Analyzer
Root runner forwarding execution to backend/run.py
"""
import os
import sys

# Ensure backend root is on Python module search path
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app import create_app
from app.extensions import db

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    print("==================================================")
    print(" Employee Productivity & Performance AI Server")
    print(" Web Interface:  http://localhost:5000")
    print(" Mobile API:     http://localhost:5000/api/v1")
    print("==================================================")
    app.run(debug=True, host="0.0.0.0", port=5000)
