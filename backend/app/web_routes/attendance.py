import csv
import io
from datetime import date, timedelta, datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.models import db
from app.models.employee import Employee
from app.models.user import User
from app.models.attendance import Attendance
from app.utils.helpers import role_required, allowed_file

attendance_bp = Blueprint("attendance", __name__)


@attendance_bp.route("/attendance")
@login_required
def list_attendance():
    if current_user.is_employee:
        emp = current_user.employee
        records = Attendance.query.filter_by(employee_id=emp.id).order_by(Attendance.date.desc()).limit(60).all()
        present = sum(1 for r in records if r.status in ("Present", "Work From Home"))
        pct = round((present / len(records)) * 100, 1) if records else 0
        return render_template("attendance.html", records=records, emp=emp, attendance_pct=pct)

    # admin / manager view — exclude admin-role users
    employees = Employee.query.outerjoin(User, Employee.user_id == User.id).filter(
        db.or_(User.role != "admin", User.id == None)
    )
    if current_user.is_manager and current_user.employee:
        employees = employees.filter(Employee.manager_id == current_user.employee.id)
    employees = employees.order_by(Employee.name).all()

    selected_date = request.args.get("date", date.today().isoformat())
    try:
        sel = datetime.strptime(selected_date, "%Y-%m-%d").date()
    except ValueError:
        sel = date.today()

    emp_ids = [e.id for e in employees]
    day_records = Attendance.query.filter(Attendance.employee_id.in_(emp_ids), Attendance.date == sel).all() \
        if emp_ids else []
    records_by_emp = {r.employee_id: r for r in day_records}

    return render_template("attendance.html", employees=employees, records_by_emp=records_by_emp,
                            selected_date=sel.isoformat())


@attendance_bp.route("/attendance/mark", methods=["POST"])
@login_required
@role_required("admin", "manager")
def mark_attendance():
    emp_id = request.form.get("employee_id", type=int)
    the_date = request.form.get("date")
    status = request.form.get("status")
    d = datetime.strptime(the_date, "%Y-%m-%d").date()

    rec = Attendance.query.filter_by(employee_id=emp_id, date=d).first()
    if not rec:
        rec = Attendance(employee_id=emp_id, date=d)
        db.session.add(rec)
    rec.status = status
    if status in ("Present", "Work From Home"):
        rec.working_hours = 8.0
    else:
        rec.working_hours = 0
    db.session.commit()
    flash("Attendance updated.", "success")
    return redirect(url_for("attendance.list_attendance", date=the_date))


@attendance_bp.route("/attendance/upload", methods=["GET", "POST"])
@login_required
@role_required("admin")
def upload_attendance():
    if request.method == "POST":
        file = request.files.get("file")
        if not file or not allowed_file(file.filename, {"csv"}):
            flash("Please upload a valid CSV file.", "danger")
            return redirect(url_for("attendance.upload_attendance"))

        stream = io.StringIO(file.stream.read().decode("utf-8"), newline=None)
        reader = csv.DictReader(stream)
        count = 0
        for row in reader:
            emp = Employee.query.filter_by(employee_code=row.get("employee_code", "").strip()).first()
            if not emp:
                continue
            d = datetime.strptime(row["date"], "%Y-%m-%d").date()
            rec = Attendance.query.filter_by(employee_id=emp.id, date=d).first() or Attendance(employee_id=emp.id, date=d)
            rec.status = row.get("status", "Present")
            rec.working_hours = float(row.get("working_hours") or 0)
            rec.overtime_hours = float(row.get("overtime_hours") or 0)
            db.session.add(rec)
            count += 1
        db.session.commit()
        flash(f"Imported {count} attendance records.", "success")
        return redirect(url_for("attendance.list_attendance"))

    return render_template("upload.html", upload_type="Attendance CSV",
                            columns=["employee_code", "date (YYYY-MM-DD)", "status", "working_hours", "overtime_hours"])
