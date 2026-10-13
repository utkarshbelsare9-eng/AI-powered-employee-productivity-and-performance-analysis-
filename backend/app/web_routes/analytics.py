from datetime import date, timedelta
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func

from app.models import db
from app.models.employee import Employee
from app.models.department import Department
from app.models.performance import Performance
from app.models.attendance import Attendance
from app.utils.helpers import current_month_str, role_required

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/analytics")
@login_required
@role_required("admin", "manager")
def analytics():
    month = current_month_str()

    dept_scores = db.session.query(
        Department.name, func.avg(Performance.performance_score)
    ).join(Employee, Employee.department_id == Department.id
           ).join(Performance, Performance.employee_id == Employee.id
                  ).filter(Performance.month == month).group_by(Department.name).all()

    grade_counts = db.session.query(
        Performance.performance_grade, func.count(Performance.id)
    ).filter(Performance.month == month).group_by(Performance.performance_grade).all()

    # Monthly trend (avg across all performance records grouped by month)
    monthly_trend = db.session.query(
        Performance.month, func.avg(Performance.performance_score)
    ).group_by(Performance.month).order_by(Performance.month).all()

    # Attendance trend last 30 days
    start = date.today() - timedelta(days=30)
    daily_attendance = db.session.query(
        Attendance.date, func.count(Attendance.id)
    ).filter(Attendance.date >= start, Attendance.status.in_(["Present", "Work From Home"])
             ).group_by(Attendance.date).order_by(Attendance.date).all()

    top10 = db.session.query(Employee.name, Performance.performance_score).join(
        Performance, Performance.employee_id == Employee.id
    ).filter(Performance.month == month).order_by(Performance.performance_score.desc()).limit(10).all()

    return render_template(
        "analytics.html",
        dept_scores=dept_scores, grade_counts=grade_counts, monthly_trend=monthly_trend,
        daily_attendance=daily_attendance, top10=top10,
    )
