"""
Trains a Random Forest classifier that predicts an employee's performance
grade (Excellent / Good / Average / Poor) from productivity features.

Run standalone:
    python machine_learning/train_model.py

This will:
  1. Load dataset/employee_performance_dataset.csv (generated if missing)
  2. Preprocess (missing values, encoding, scaling)
  3. Train/test split + cross validation
  4. Report Accuracy / Precision / Recall / F1 / Confusion Matrix
  5. Save feature importance chart to static/images/feature_importance.png
  6. Save the trained model + scaler + label encoder to model/
"""

import os
import sys
import json
import numpy as np
import pandas as pd
import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report
)

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.dirname(APP_DIR)
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)

DATASET_PATH = os.path.join(PROJECT_ROOT, "datasets", "employee_performance_dataset.csv")
MODEL_DIR = os.path.join(PROJECT_ROOT, "ml_artifacts")
IMAGES_DIR = os.path.join(PROJECT_ROOT, "frontend", "web", "static", "images")

os.makedirs(os.path.dirname(DATASET_PATH), exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

FEATURES = [
    "attendance_percent", "avg_working_hours", "late_entries", "leave_days",
    "tasks_assigned", "tasks_completed", "deadlines_missed", "overtime_hours",
    "customer_rating", "manager_rating", "skill_score", "experience_years",
]
TARGET = "performance_grade"


def generate_synthetic_dataset(n=1200, seed=42):
    """Creates a realistic synthetic dataset so the app is trainable out of
    the box without requiring the user to source real HR data."""
    rng = np.random.default_rng(seed)

    attendance_percent = np.clip(rng.normal(88, 9, n), 40, 100)
    avg_working_hours = np.clip(rng.normal(8.2, 1.1, n), 3, 13)
    late_entries = np.clip(rng.poisson(2, n), 0, 20)
    leave_days = np.clip(rng.poisson(3, n), 0, 25)
    tasks_assigned = np.clip(rng.normal(28, 8, n), 5, 60).astype(int)
    completion_ratio = np.clip(rng.normal(0.82, 0.15, n), 0.2, 1.0)
    tasks_completed = (tasks_assigned * completion_ratio).astype(int)
    deadlines_missed = np.clip((tasks_assigned - tasks_completed) * rng.uniform(0.2, 0.8, n), 0, None).astype(int)
    overtime_hours = np.clip(rng.normal(6, 5, n), 0, 40)
    customer_rating = np.clip(rng.normal(3.8, 0.7, n), 1, 5)
    manager_rating = np.clip(rng.normal(3.7, 0.8, n), 1, 5)
    skill_score = np.clip(rng.normal(70, 14, n), 20, 100)
    experience_years = np.clip(rng.exponential(4, n), 0, 25)

    df = pd.DataFrame({
        "attendance_percent": attendance_percent,
        "avg_working_hours": avg_working_hours,
        "late_entries": late_entries,
        "leave_days": leave_days,
        "tasks_assigned": tasks_assigned,
        "tasks_completed": tasks_completed,
        "deadlines_missed": deadlines_missed,
        "overtime_hours": overtime_hours,
        "customer_rating": customer_rating,
        "manager_rating": manager_rating,
        "skill_score": skill_score,
        "experience_years": experience_years,
    })

    # Composite score used to derive a realistic ground-truth label
    completion_rate = df.tasks_completed / df.tasks_assigned.replace(0, 1)
    score = (
        df.attendance_percent * 0.22
        + completion_rate * 100 * 0.28
        + df.manager_rating * 20 * 0.18
        + df.customer_rating * 20 * 0.12
        + df.skill_score * 0.12
        - df.late_entries * 1.2
        - df.deadlines_missed * 2.0
        + rng.normal(0, 5, n)
    )

    def grade(s):
        if s >= 85:
            return "Excellent"
        elif s >= 70:
            return "Good"
        elif s >= 55:
            return "Average"
        return "Poor"

    df[TARGET] = score.apply(grade)
    return df


def load_or_create_dataset():
    os.makedirs(os.path.dirname(DATASET_PATH), exist_ok=True)
    if not os.path.exists(DATASET_PATH):
        df = generate_synthetic_dataset()
        df.to_csv(DATASET_PATH, index=False)
        print(f"[INFO] Synthetic dataset created at {DATASET_PATH}")
    else:
        df = pd.read_csv(DATASET_PATH)
        print(f"[INFO] Loaded existing dataset from {DATASET_PATH}")
    return df


def preprocess(df):
    df = df.copy()
    # Handle missing values
    for col in FEATURES:
        if df[col].isnull().any():
            df[col] = df[col].fillna(df[col].median())
    df = df.dropna(subset=[TARGET])
    return df


def train():
    os.makedirs(MODEL_DIR, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)

    df = load_or_create_dataset()
    df = preprocess(df)

    X = df[FEATURES]
    y = df[TARGET]

    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
    )

    model = RandomForestClassifier(
        n_estimators=300, max_depth=12, min_samples_split=4,
        random_state=42, class_weight="balanced", n_jobs=-1
    )
    model.fit(X_train, y_train)

    # Cross validation
    cv_scores = cross_val_score(model, X_scaled, y_encoded, cv=5)

    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, average="weighted", zero_division=0)
    rec = recall_score(y_test, y_pred, average="weighted", zero_division=0)
    f1 = f1_score(y_test, y_pred, average="weighted", zero_division=0)
    cm = confusion_matrix(y_test, y_pred)
    report = classification_report(y_test, y_pred, target_names=label_encoder.classes_, zero_division=0)

    print("=" * 60)
    print("MODEL TRAINING RESULTS")
    print("=" * 60)
    print(f"Accuracy:           {acc:.4f}")
    print(f"Precision (wtd):    {prec:.4f}")
    print(f"Recall (wtd):       {rec:.4f}")
    print(f"F1 Score (wtd):     {f1:.4f}")
    print(f"Cross-Val Accuracy: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")
    print("\nConfusion Matrix:")
    print(cm)
    print("\nClassification Report:")
    print(report)

    # Feature importance chart
    importances = model.feature_importances_
    order = np.argsort(importances)
    plt.figure(figsize=(8, 6))
    plt.barh(np.array(FEATURES)[order], importances[order], color="#6C5CE7")
    plt.title("Feature Importance - Employee Performance Model")
    plt.xlabel("Importance")
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGES_DIR, "feature_importance.png"), dpi=140)
    plt.close()

    # Confusion matrix chart
    plt.figure(figsize=(6, 5))
    plt.imshow(cm, cmap="Purples")
    plt.title("Confusion Matrix")
    plt.colorbar()
    ticks = np.arange(len(label_encoder.classes_))
    plt.xticks(ticks, label_encoder.classes_, rotation=45)
    plt.yticks(ticks, label_encoder.classes_)
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            plt.text(j, i, cm[i, j], ha="center", va="center",
                      color="white" if cm[i, j] > cm.max() / 2 else "black")
    plt.ylabel("True label")
    plt.xlabel("Predicted label")
    plt.tight_layout()
    plt.savefig(os.path.join(IMAGES_DIR, "confusion_matrix.png"), dpi=140)
    plt.close()

    # Persist artifacts
    joblib.dump(model, os.path.join(MODEL_DIR, "performance_model.joblib"))
    joblib.dump(scaler, os.path.join(MODEL_DIR, "scaler.joblib"))
    joblib.dump(label_encoder, os.path.join(MODEL_DIR, "label_encoder.joblib"))

    metrics = {
        "accuracy": acc, "precision": prec, "recall": rec, "f1_score": f1,
        "cv_mean_accuracy": float(cv_scores.mean()),
        "cv_std": float(cv_scores.std()),
        "classes": label_encoder.classes_.tolist(),
        "confusion_matrix": cm.tolist(),
        "feature_importance": dict(zip(FEATURES, importances.tolist())),
        "n_samples": len(df),
    }
    with open(os.path.join(MODEL_DIR, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"\n[INFO] Model + scaler + encoder saved to {MODEL_DIR}")
    print(f"[INFO] Metrics saved to {os.path.join(MODEL_DIR, 'metrics.json')}")
    return metrics


if __name__ == "__main__":
    train()
