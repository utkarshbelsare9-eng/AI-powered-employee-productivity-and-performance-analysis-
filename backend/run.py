import os
import sys

# Set directory paths
BACKEND_DIR = os.path.abspath(os.path.dirname(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app import create_app
from app.extensions import db
from app.config import Config

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        # Ensure database tables exist without recreating or dropping data
        db.create_all()

        # Check for ML model artifacts
        model_path = os.path.join(app.config["MODEL_FOLDER"], "performance_model.joblib")
        if not os.path.exists(model_path):
            print("[INFO] No trained model found in ml_artifacts/. Training now...")
            from app.machine_learning.train_model import train
            train()

    # Launch application
    print("==================================================")
    print(" Employee Productivity & Performance AI Server")
    print(" Web Interface:  http://localhost:5000")
    print(" Mobile API:     http://localhost:5000/api/v1")
    print("==================================================")
    app.run(debug=True, host="0.0.0.0", port=5000)
