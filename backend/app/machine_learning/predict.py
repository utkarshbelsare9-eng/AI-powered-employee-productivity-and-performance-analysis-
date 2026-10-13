"""
Loads the trained model artifacts and exposes a simple predict() function
used by the Flask app to score employees and generate recommendations.
"""

import os
import json
import joblib
import numpy as np

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BACKEND_DIR))

# Prioritize ml_artifacts at project root, fallback to backend/model
if os.path.exists(os.path.join(PROJECT_ROOT, "ml_artifacts")):
    MODEL_DIR = os.path.join(PROJECT_ROOT, "ml_artifacts")
else:
    MODEL_DIR = os.path.join(BACKEND_DIR, "model")

FEATURES = [
    "attendance_percent", "avg_working_hours", "late_entries", "leave_days",
    "tasks_assigned", "tasks_completed", "deadlines_missed", "overtime_hours",
    "customer_rating", "manager_rating", "skill_score", "experience_years",
]

_model = None
_scaler = None
_label_encoder = None


def _load_artifacts():
    global _model, _scaler, _label_encoder
    if _model is None:
        model_path = os.path.join(MODEL_DIR, "performance_model.joblib")
        scaler_path = os.path.join(MODEL_DIR, "scaler.joblib")
        encoder_path = os.path.join(MODEL_DIR, "label_encoder.joblib")
        if not (os.path.exists(model_path) and os.path.exists(scaler_path) and os.path.exists(encoder_path)):
            # Train on the fly if artifacts don't exist yet
            from app.machine_learning.train_model import train
            train()
        _model = joblib.load(model_path)
        _scaler = joblib.load(scaler_path)
        _label_encoder = joblib.load(encoder_path)
    return _model, _scaler, _label_encoder


def predict_employee(feature_dict):
    """feature_dict must contain all keys in FEATURES.
    Returns dict with grade, confidence, probabilities, risk scores, recommendations."""
    model, scaler, label_encoder = _load_artifacts()

    x = np.array([[feature_dict.get(f, 0) for f in FEATURES]])
    x_scaled = scaler.transform(x)

    pred_idx = model.predict(x_scaled)[0]
    proba = model.predict_proba(x_scaled)[0]
    grade = label_encoder.inverse_transform([pred_idx])[0]
    confidence = float(np.max(proba) * 100)
    probabilities = {cls: float(p * 100) for cls, p in zip(label_encoder.classes_, proba)}

    # --- Derived AI insights (rule-based, explainable, layered on top of ML output) ---
    attrition_risk = _attrition_risk(feature_dict, grade)
    burnout_risk = _burnout_risk(feature_dict)
    risk_level = "High" if max(attrition_risk, burnout_risk) >= 65 else (
        "Medium" if max(attrition_risk, burnout_risk) >= 35 else "Low")
    promotion_eligible = grade in ("Excellent", "Good") and feature_dict.get("manager_rating", 0) >= 4 \
        and feature_dict.get("deadlines_missed", 99) <= 2
    recommendations = generate_recommendations(feature_dict, grade)

    return {
        "grade": grade,
        "predicted_grade": grade,
        "confidence": round(confidence, 1),
        "probabilities": probabilities,
        "attrition_risk_percent": round(attrition_risk, 1),
        "burnout_risk_percent": round(burnout_risk, 1),
        "attrition_risk": "High" if attrition_risk >= 65 else ("Medium" if attrition_risk >= 35 else "Low"),
        "burnout_risk": "High" if burnout_risk >= 65 else ("Medium" if burnout_risk >= 35 else "Low"),
        "risk_level": risk_level,
        "promotion_eligible": bool(promotion_eligible),
        "recommendations": recommendations,
    }


def _attrition_risk(f, grade):
    risk = 0
    risk += max(0, (90 - f.get("attendance_percent", 90))) * 0.9
    risk += min(f.get("overtime_hours", 0), 40) * 0.8
    risk += (5 - f.get("manager_rating", 3)) * 8
    risk += 15 if grade == "Poor" else (5 if grade == "Average" else 0)
    risk -= f.get("experience_years", 0) * 0.3  # tenure slightly reduces flight risk
    return float(np.clip(risk, 0, 100))


def _burnout_risk(f):
    risk = 0
    risk += min(f.get("overtime_hours", 0), 40) * 1.3
    risk += max(0, f.get("avg_working_hours", 8) - 8) * 6
    risk += f.get("deadlines_missed", 0) * 2.5
    risk -= max(0, f.get("attendance_percent", 90) - 85) * 0.5
    return float(np.clip(risk, 0, 100))


def generate_recommendations(f, grade):
    recs = []
    if f.get("attendance_percent", 100) < 85:
        recs.append("Improve attendance consistency to boost overall reliability score.")
    if f.get("late_entries", 0) > 4:
        recs.append("Reduce late entries — consider adjusting shift start time or commute planning.")
    if f.get("deadlines_missed", 0) > 2:
        recs.append("Reduce deadline misses by improving task time estimation and prioritization.")
    if f.get("overtime_hours", 0) > 20:
        recs.append("High overtime detected — redistribute workload to prevent burnout.")
    if f.get("skill_score", 100) < 60:
        recs.append("Enroll in advanced skill-development / certification training.")
    if f.get("customer_rating", 5) < 3.5:
        recs.append("Focus on communication and client-facing collaboration skills.")
    if f.get("manager_rating", 5) < 3.5:
        recs.append("Schedule regular 1:1s with manager to realign on expectations.")
    if grade in ("Excellent", "Good") and f.get("manager_rating", 0) >= 4 and f.get("deadlines_missed", 99) <= 2:
        recs.append("Eligible for promotion — consider for next performance review cycle.")
    if grade == "Excellent" and f.get("experience_years", 0) >= 3:
        recs.append("Ready for a leadership / mentoring role.")
    if grade == "Poor":
        recs.append("Needs structured mentoring and a personalized improvement plan.")
    if not recs:
        recs.append("Performing well across all tracked metrics — keep up the consistency!")
    return recs
