from datetime import date, timedelta
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from sqlalchemy import func

from app.models import db
from app.models.employee import Employee
from app.models.department import Department
from app.models.attendance import Attendance
from app.models.task import Task
from app.models.performance import Performance
from app.models.notification import Notification
from app.utils.helpers import current_month_str

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@dashboard_bp.route("/dashboard")
@login_required
def index():
    today = date.today()
    month = current_month_str()

    if current_user.is_admin:
        total_employees = Employee.query.filter(Employee.status == "Active").count()
        present_today = Attendance.query.filter(
            Attendance.date == today, Attendance.status.in_(["Present", "Work From Home"])
        ).count()
        absent_today = Attendance.query.filter(Attendance.date == today, Attendance.status == "Absent").count()

        avg_productivity = db.session.query(func.avg(Performance.productivity_score)).filter(
            Performance.month == month).scalar() or 0
        avg_attendance = db.session.query(func.avg(Performance.attendance_percent)).filter(
            Performance.month == month).scalar() or 0

        top_performer = db.session.query(Employee, Performance).join(
            Performance, Performance.employee_id == Employee.id
        ).filter(Performance.month == month).order_by(Performance.performance_score.desc()).first()

        bottom_performer = db.session.query(Employee, Performance).join(
            Performance, Performance.employee_id == Employee.id
        ).filter(Performance.month == month).order_by(Performance.performance_score.asc()).first()

        dept_performance = db.session.query(
            Department.name, func.avg(Performance.performance_score)
        ).join(Employee, Employee.department_id == Department.id
               ).join(Performance, Performance.employee_id == Employee.id
                      ).filter(Performance.month == month
                               ).group_by(Department.name).all()

        recent_notifications = Notification.query.order_by(Notification.created_at.desc()).limit(6).all()

        return render_template(
            "dashboard.html",
            total_employees=total_employees, present_today=present_today, absent_today=absent_today,
            avg_productivity=round(avg_productivity, 1), avg_attendance=round(avg_attendance, 1),
            top_performer=top_performer, bottom_performer=bottom_performer,
            dept_performance=dept_performance, notifications=recent_notifications,
        )

    elif current_user.is_manager:
        mgr_emp = current_user.employee
        team = Employee.query.filter_by(manager_id=mgr_emp.id).all() if mgr_emp else []
        team_ids = [e.id for e in team]

        present_today = Attendance.query.filter(
            Attendance.employee_id.in_(team_ids), Attendance.date == today,
            Attendance.status.in_(["Present", "Work From Home"])
        ).count() if team_ids else 0

        pending_tasks = Task.query.filter(
            Task.employee_id.in_(team_ids), Task.status.in_(["Pending", "In Progress"])
        ).count() if team_ids else 0

        team_perf = Performance.query.filter(
            Performance.employee_id.in_(team_ids), Performance.month == month
        ).all() if team_ids else []
        avg_team_score = round(sum(p.performance_score for p in team_perf) / len(team_perf), 1) if team_perf else 0

        notifications = Notification.query.filter_by(user_id=current_user.id).order_by(
            Notification.created_at.desc()).limit(6).all()

        return render_template(
            "dashboard.html", team=team, present_today=present_today, pending_tasks=pending_tasks,
            avg_team_score=avg_team_score, team_perf=team_perf, notifications=notifications,
        )

    else:  # employee
        emp = current_user.employee
        perf = Performance.query.filter_by(employee_id=emp.id, month=month).first() if emp else None
        tasks = Task.query.filter_by(employee_id=emp.id).order_by(Task.deadline.asc()).limit(6).all() if emp else []
        recent_attendance = Attendance.query.filter_by(employee_id=emp.id).order_by(
            Attendance.date.desc()).limit(14).all() if emp else []
        notifications = Notification.query.filter_by(user_id=current_user.id).order_by(
            Notification.created_at.desc()).limit(6).all()

        return render_template(
            "dashboard.html", emp=emp, perf=perf, tasks=tasks,
            recent_attendance=recent_attendance, notifications=notifications,
        )
