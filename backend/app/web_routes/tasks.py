import csv
import io
from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.models import db
from app.models.employee import Employee
from app.models.user import User
from app.models.task import Task
from app.utils.helpers import role_required, allowed_file

tasks_bp = Blueprint("tasks", __name__)


@tasks_bp.route("/tasks")
@login_required
def list_tasks():
    if current_user.is_employee:
        emp = current_user.employee
        tasks = Task.query.filter_by(employee_id=emp.id).order_by(Task.deadline.asc()).all() if emp else []
        return render_template("tasks.html", tasks=tasks, employees=None)

    employees = Employee.query.outerjoin(User, Employee.user_id == User.id).filter(
        db.or_(User.role != "admin", User.id == None)
    )
    if current_user.is_manager and current_user.employee:
        employees = employees.filter(Employee.manager_id == current_user.employee.id)
    employees = employees.order_by(Employee.name).all()
    emp_ids = [e.id for e in employees]

    status = request.args.get("status", "")
    query = Task.query.filter(Task.employee_id.in_(emp_ids)) if emp_ids else Task.query.filter(False)
    if status:
        query = query.filter(Task.status == status)
    tasks = query.order_by(Task.deadline.asc()).limit(200).all()

    return render_template("tasks.html", tasks=tasks, employees=employees, status=status)


@tasks_bp.route("/tasks/add", methods=["GET", "POST"])
@login_required
@role_required("admin", "manager")
def add_task():
    employees = Employee.query.outerjoin(User, Employee.user_id == User.id).filter(
        db.or_(User.role != "admin", User.id == None)
    )
    if current_user.is_manager and current_user.employee:
        employees = employees.filter(Employee.manager_id == current_user.employee.id)
    employees = employees.order_by(Employee.name).all()

    if request.method == "POST":
        f = request.form
        task = Task(
            employee_id=f.get("employee_id", type=int), title=f.get("title"),
            category=f.get("category"), priority=f.get("priority", "Medium"),
            status=f.get("status", "Pending"), completed_percent=f.get("completed_percent", type=int) or 0,
            estimated_hours=f.get("estimated_hours", type=float) or 0,
            assigned_date=date.today(),
            deadline=datetime.strptime(f.get("deadline"), "%Y-%m-%d").date() if f.get("deadline") else None,
        )
        db.session.add(task)
        db.session.commit()
        flash("Task assigned successfully.", "success")
        return redirect(url_for("tasks.list_tasks"))

    return render_template("task_form.html", employees=employees)


@tasks_bp.route("/tasks/<int:task_id>/update", methods=["POST"])
@login_required
def update_task_status(task_id):
    task = Task.query.get_or_404(task_id)
    if current_user.is_employee and (not current_user.employee or task.employee_id != current_user.employee.id):
        flash("You can only update your own tasks.", "danger")
        return redirect(url_for("tasks.list_tasks"))

    task.status = request.form.get("status", task.status)
    task.completed_percent = request.form.get("completed_percent", type=int) or task.completed_percent
    task.actual_hours = request.form.get("actual_hours", type=float) or task.actual_hours
    if task.status == "Completed" and not task.completion_date:
        task.completion_date = date.today()
    db.session.commit()
    flash("Task updated.", "success")
    return redirect(url_for("tasks.list_tasks"))


@tasks_bp.route("/tasks/upload", methods=["GET", "POST"])
@login_required
@role_required("admin")
def upload_tasks():
    if request.method == "POST":
        file = request.files.get("file")
        if not file or not allowed_file(file.filename, {"csv"}):
            flash("Please upload a valid CSV file.", "danger")
            return redirect(url_for("tasks.upload_tasks"))
        stream = io.StringIO(file.stream.read().decode("utf-8"), newline=None)
        reader = csv.DictReader(stream)
        count = 0
        for row in reader:
            emp = Employee.query.filter_by(employee_code=row.get("employee_code", "").strip()).first()
            if not emp:
                continue
            db.session.add(Task(
                employee_id=emp.id, title=row.get("title"), category=row.get("category"),
                priority=row.get("priority", "Medium"), status=row.get("status", "Pending"),
                completed_percent=int(row.get("completed_percent") or 0),
                estimated_hours=float(row.get("estimated_hours") or 0),
                actual_hours=float(row.get("actual_hours") or 0),
                deadline=datetime.strptime(row["deadline"], "%Y-%m-%d").date() if row.get("deadline") else None,
            ))
            count += 1
        db.session.commit()
        flash(f"Imported {count} tasks.", "success")
        return redirect(url_for("tasks.list_tasks"))

    return render_template("upload.html", upload_type="Task CSV",
                            columns=["employee_code", "title", "category", "priority", "status",
                                     "completed_percent", "estimated_hours", "actual_hours", "deadline (YYYY-MM-DD)"])
