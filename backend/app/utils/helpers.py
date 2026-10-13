import os
import calendar
from datetime import datetime, date, timedelta
from functools import wraps
from flask import abort
from flask_login import current_user


def role_required(*roles):
    """Decorator restricting a route to specific user roles."""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.role not in roles:
                abort(403)
            return f(*args, **kwargs)
        return wrapped
    return decorator


def allowed_file(filename, allowed_ext):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_ext


def current_month_str():
    return date.today().strftime("%Y-%m")


def month_label(month_str):
    y, m = month_str.split("-")
    return f"{calendar.month_name[int(m)]} {y}"


def days_in_month(month_str):
    y, m = map(int, month_str.split("-"))
    return calendar.monthrange(y, m)[1]


def grade_badge_class(grade):
    return {
        "Excellent": "success",
        "Good": "primary",
        "Average": "warning",
        "Poor": "danger",
    }.get(grade, "secondary")


def risk_badge_class(level):
    return {"Low": "success", "Medium": "warning", "High": "danger"}.get(level, "secondary")


def compute_productivity_metrics(attendance_percent, task_completion_rate, overtime_hours,
                                  late_entries, working_days, manager_rating, customer_rating):
    """Rule-based composite scoring used for dashboards & AI module,
    complementary to the ML classification model."""
    punctuality_score = max(0, 100 - (late_entries / max(working_days, 1)) * 100 * 3)
    overtime_score = max(0, 100 - min(overtime_hours, 40) * 2)
    time_management_score = (punctuality_score * 0.5) + (overtime_score * 0.5)
    work_efficiency = min(100, task_completion_rate * 0.7 + attendance_percent * 0.3)
    consistency_score = min(100, (attendance_percent + task_completion_rate) / 2)

    productivity_score = round(
        attendance_percent * 0.25 +
        task_completion_rate * 0.35 +
        time_management_score * 0.20 +
        work_efficiency * 0.20, 1
    )
    performance_score = round(
        productivity_score * 0.5 +
        (manager_rating / 5 * 100) * 0.3 +
        (customer_rating / 5 * 100) * 0.2, 1
    )
    return {
        "punctuality_score": round(punctuality_score, 1),
        "overtime_score": round(overtime_score, 1),
        "time_management_score": round(time_management_score, 1),
        "work_efficiency": round(work_efficiency, 1),
        "consistency_score": round(consistency_score, 1),
        "productivity_score": productivity_score,
        "performance_score": performance_score,
    }


def score_to_grade(score):
    if score >= 85:
        return "Excellent"
    elif score >= 70:
        return "Good"
    elif score >= 55:
        return "Average"
    return "Poor"
