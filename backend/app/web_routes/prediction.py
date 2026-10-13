import json
from datetime import date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import func

from app.models import db
from app.models.employee import Employee
from app.models.user import User
from app.models.attendance import Attendance
from app.models.task import Task
from app.models.performance import Performance
from app.models.prediction import Prediction
from app.utils.helpers import role_required, current_month_str, grade_badge_class, risk_badge_class
from app.machine_learning.predict import predict_employee

prediction_bp = Blueprint("prediction", __name__)


def _build_features(emp):
    """Aggregate an employee's last 30 days of attendance/task data into ML features."""
    start = date.today() - timedelta(days=30)
    att = Attendance.query.filter(Attendance.employee_id == emp.id, Attendance.date >= start).all()
    working_days = len(att) or 1
    present_days = sum(1 for a in att if a.status in ("Present", "Work From Home"))
    late = sum(1 for a in att if a.late_entry)
    leave_days = sum(1 for a in att if a.status == "Leave")
    total_hours = sum(a.working_hours or 0 for a in att)
    total_ot = sum(a.overtime_hours or 0 for a in att)

    tasks = Task.query.filter(Task.employee_id == emp.id, Task.assigned_date >= start).all()
    n_tasks = len(tasks) or 1
    completed = sum(1 for t in tasks if t.status == "Completed")
    missed = sum(1 for t in tasks if t.is_delayed)

    latest_perf = Performance.query.filter_by(employee_id=emp.id).order_by(Performance.month.desc()).first()
    manager_rating = latest_perf.manager_rating if latest_perf else 3.5
    customer_rating = latest_perf.customer_rating if latest_perf else 3.5
    skill_score = latest_perf.skill_score if latest_perf else 60

    return {
        "attendance_percent": round((present_days / working_days) * 100, 1),
        "avg_working_hours": round(total_hours / max(present_days, 1), 1),
        "late_entries": late,
        "leave_days": leave_days,
        "tasks_assigned": len(tasks),
        "tasks_completed": completed,
        "deadlines_missed": missed,
        "overtime_hours": round(total_ot, 1),
        "customer_rating": customer_rating,
        "manager_rating": manager_rating,
        "skill_score": skill_score,
        "experience_years": emp.experience_years or 0,
    }


@prediction_bp.route("/prediction")
@prediction_bp.route("/prediction/<int:emp_id>")
@login_required
def prediction(emp_id=None):
    if current_user.is_employee:
        emp = current_user.employee
    elif emp_id:
        emp = Employee.query.get_or_404(emp_id)
    else:
        employees = Employee.query.outerjoin(User, Employee.user_id == User.id).filter(
            db.or_(User.role != "admin", User.id == None)
        ).order_by(Employee.name).all()
        return render_template("prediction.html", select_mode=True, employees=employees)

    if not emp:
        flash("No employee profile linked to this account.", "warning")
        return redirect(url_for("dashboard.index"))

    features = _build_features(emp)
    result = predict_employee(features)

    latest = Prediction.query.filter_by(employee_id=emp.id).order_by(Prediction.created_at.desc()).first()

    return render_template(
        "prediction.html", select_mode=False, emp=emp, features=features, result=result,
        latest=latest, grade_badge_class=grade_badge_class, risk_badge_class=risk_badge_class,
    )


@prediction_bp.route("/prediction/<int:emp_id>/save", methods=["POST"])
@login_required
@role_required("admin", "manager")
def save_prediction(emp_id):
    emp = Employee.query.get_or_404(emp_id)
    features = _build_features(emp)
    result = predict_employee(features)

    pred = Prediction(
        employee_id=emp.id, predicted_grade=result["grade"], confidence=result["confidence"],
        probabilities=json.dumps(result["probabilities"]), risk_level=result["risk_level"],
        attrition_risk_percent=result["attrition_risk_percent"],
        burnout_risk_percent=result["burnout_risk_percent"],
        promotion_eligible=result["promotion_eligible"],
        recommendations=json.dumps(result["recommendations"]),
    )
    db.session.add(pred)
    db.session.commit()
    flash(f"AI prediction saved for {emp.name}.", "success")
    return redirect(url_for("prediction.prediction", emp_id=emp.id))


@prediction_bp.route("/recommendation")
@prediction_bp.route("/recommendation/<int:emp_id>")
@login_required
def recommendation(emp_id=None):
    if current_user.is_employee:
        emp = current_user.employee
    elif emp_id:
        emp = Employee.query.get_or_404(emp_id)
    else:
        employees = Employee.query.outerjoin(User, Employee.user_id == User.id).filter(
            db.or_(User.role != "admin", User.id == None)
        ).order_by(Employee.name).all()
        return render_template("recommendation.html", select_mode=True, employees=employees)

    if not emp:
        flash("No employee profile linked to this account.", "warning")
        return redirect(url_for("dashboard.index"))

    features = _build_features(emp)
    result = predict_employee(features)

    return render_template(
        "recommendation.html", select_mode=False, emp=emp, result=result,
        grade_badge_class=grade_badge_class,
    )
