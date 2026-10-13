from datetime import date, timedelta
from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func

from app.models import db
from app.models.employee import Employee
from app.models.department import Department
from app.models.performance import Performance
from app.models.attendance import Attendance
from app.utils.helpers import current_month_str

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/charts/department-performance")
@login_required
def department_performance():
    month = current_month_str()
    rows = db.session.query(Department.name, func.avg(Performance.performance_score)).join(
        Employee, Employee.department_id == Department.id).join(
        Performance, Performance.employee_id == Employee.id).filter(
        Performance.month == month).group_by(Department.name).all()
    return jsonify({"labels": [r[0] for r in rows], "values": [round(r[1], 1) for r in rows]})


@api_bp.route("/charts/grade-distribution")
@login_required
def grade_distribution():
    month = current_month_str()
    rows = db.session.query(Performance.performance_grade, func.count(Performance.id)).filter(
        Performance.month == month).group_by(Performance.performance_grade).all()
    order = ["Excellent", "Good", "Average", "Poor"]
    data = dict(rows)
    return jsonify({"labels": order, "values": [data.get(g, 0) for g in order]})


@api_bp.route("/charts/attendance-trend")
@login_required
def attendance_trend():
    start = date.today() - timedelta(days=14)
    rows = db.session.query(Attendance.date, func.count(Attendance.id)).filter(
        Attendance.date >= start, Attendance.status.in_(["Present", "Work From Home"])
    ).group_by(Attendance.date).order_by(Attendance.date).all()
    return jsonify({"labels": [r[0].strftime("%d %b") for r in rows], "values": [r[1] for r in rows]})


@api_bp.route("/charts/monthly-trend")
@login_required
def monthly_trend():
    rows = db.session.query(Performance.month, func.avg(Performance.performance_score)).group_by(
        Performance.month).order_by(Performance.month).all()
    return jsonify({"labels": [r[0] for r in rows], "values": [round(r[1], 1) for r in rows]})
