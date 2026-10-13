import os
import csv
import io
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user

from app.models import db
from app.models.user import User
from app.models.employee import Employee
from app.models.department import Department
from app.models.skill import Skill
from app.utils.helpers import role_required, allowed_file

employees_bp = Blueprint("employees", __name__)


@employees_bp.route("/employees")
@login_required
def list_employees():
    q = request.args.get("q", "").strip()
    dept_id = request.args.get("department", type=int)
    status = request.args.get("status", "")

    query = Employee.query.outerjoin(User, Employee.user_id == User.id).filter(
        db.or_(User.role != "admin", User.id == None)
    )
    if current_user.is_manager and current_user.employee:
        query = query.filter(Employee.manager_id == current_user.employee.id)
    if q:
        query = query.filter(Employee.name.ilike(f"%{q}%") | Employee.employee_code.ilike(f"%{q}%"))
    if dept_id:
        query = query.filter(Employee.department_id == dept_id)
    if status:
        query = query.filter(Employee.status == status)

    employees = query.order_by(Employee.employee_code).all()
    departments = Department.query.order_by(Department.name).all()
    return render_template("employee.html", employees=employees, departments=departments,
                            q=q, dept_id=dept_id, status=status)


@employees_bp.route("/employees/add", methods=["GET", "POST"])
@login_required
@role_required("admin")
def add_employee():
    departments = Department.query.order_by(Department.name).all()
    managers = Employee.query.order_by(Employee.name).all()

    if request.method == "POST":
        f = request.form
        last_code = db.session.query(Employee).order_by(Employee.id.desc()).first()
        next_num = (last_code.id + 1) if last_code else 1
        emp_code = f"EMP-{next_num:04d}"

        username = f.get("username") or f"emp{next_num}"
        if not User.query.filter_by(username=username).first():
            user = User(username=username, email=f.get("email"), role="employee")
            user.set_password(f.get("password") or "Employee@123")
            db.session.add(user)
            db.session.flush()
            user_id = user.id
        else:
            user_id = None

        emp = Employee(
            employee_code=emp_code, user_id=user_id, name=f.get("name"), email=f.get("email"),
            phone=f.get("phone"), gender=f.get("gender"), age=f.get("age", type=int),
            designation=f.get("designation"), salary=f.get("salary", type=float),
            joining_date=datetime.strptime(f.get("joining_date"), "%Y-%m-%d").date() if f.get("joining_date") else None,
            address=f.get("address"), experience_years=f.get("experience_years", type=float) or 0,
            education=f.get("education"), status=f.get("status", "Active"),
            department_id=f.get("department_id", type=int),
            manager_id=f.get("manager_id", type=int) or None,
        )
        db.session.add(emp)
        db.session.commit()
        flash(f"Employee {emp.name} ({emp.employee_code}) added successfully.", "success")
        return redirect(url_for("employees.list_employees"))

    return render_template("employee_form.html", departments=departments, managers=managers, employee=None)


@employees_bp.route("/employees/<int:emp_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("admin", "manager")
def edit_employee(emp_id):
    emp = Employee.query.get_or_404(emp_id)
    departments = Department.query.order_by(Department.name).all()
    managers = Employee.query.filter(Employee.id != emp_id).order_by(Employee.name).all()

    if request.method == "POST":
        f = request.form
        emp.name = f.get("name")
        emp.email = f.get("email")
        emp.phone = f.get("phone")
        emp.gender = f.get("gender")
        emp.age = f.get("age", type=int)
        emp.designation = f.get("designation")
        if current_user.is_admin:
            emp.salary = f.get("salary", type=float)
        emp.address = f.get("address")
        emp.experience_years = f.get("experience_years", type=float) or 0
        emp.education = f.get("education")
        emp.status = f.get("status", emp.status)
        emp.department_id = f.get("department_id", type=int)
        emp.manager_id = f.get("manager_id", type=int) or None
        db.session.commit()
        flash(f"Employee {emp.name} updated successfully.", "success")
        return redirect(url_for("employees.list_employees"))

    return render_template("employee_form.html", departments=departments, managers=managers, employee=emp)


@employees_bp.route("/employees/<int:emp_id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_employee(emp_id):
    emp = Employee.query.get_or_404(emp_id)
    name = emp.name
    if emp.user_id:
        user = User.query.get(emp.user_id)
        if user:
            db.session.delete(user)
    db.session.delete(emp)
    db.session.commit()
    flash(f"Employee {name} deleted.", "info")
    return redirect(url_for("employees.list_employees"))


@employees_bp.route("/employees/<int:emp_id>")
@login_required
def view_employee(emp_id):
    emp = Employee.query.get_or_404(emp_id)
    from app.web_routes.activity import build_timesheet_rows
    timesheet_rows = build_timesheet_rows(emp.id, num_days=7)
    return render_template("profile.html", emp=emp, is_own_profile=False, timesheet_rows=timesheet_rows)


@employees_bp.route("/departments", methods=["GET", "POST"])
@login_required
@role_required("admin")
def departments():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        desc = request.form.get("description", "")
        if name and not Department.query.filter_by(name=name).first():
            db.session.add(Department(name=name, description=desc))
            db.session.commit()
            flash(f"Department '{name}' created.", "success")
        else:
            flash("Department name is required and must be unique.", "warning")
        return redirect(url_for("employees.departments"))

    depts = Department.query.order_by(Department.name).all()
    return render_template("departments.html", departments=depts)


@employees_bp.route("/departments/<int:dept_id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_department(dept_id):
    dep = Department.query.get_or_404(dept_id)
    if dep.employees:
        flash("Cannot delete a department with assigned employees.", "danger")
    else:
        db.session.delete(dep)
        db.session.commit()
        flash("Department deleted.", "info")
    return redirect(url_for("employees.departments"))


@employees_bp.route("/employees/upload", methods=["GET", "POST"])
@login_required
@role_required("admin")
def upload_employees():
    if request.method == "POST":
        file = request.files.get("file")
        if not file or not allowed_file(file.filename, {"csv"}):
            flash("Please upload a valid CSV file.", "danger")
            return redirect(url_for("employees.upload_employees"))

        stream = io.StringIO(file.stream.read().decode("utf-8"), newline=None)
        reader = csv.DictReader(stream)
        count = 0
        last = db.session.query(Employee).order_by(Employee.id.desc()).first()
        next_num = (last.id + 1) if last else 1

        for row in reader:
            dept = Department.query.filter_by(name=row.get("department", "").strip()).first()
            emp = Employee(
                employee_code=f"EMP-{next_num:04d}",
                name=row.get("name"), email=row.get("email"), phone=row.get("phone"),
                gender=row.get("gender"), age=int(row["age"]) if row.get("age") else None,
                designation=row.get("designation"), salary=float(row["salary"]) if row.get("salary") else None,
                status=row.get("status", "Active"), department_id=dept.id if dept else None,
            )
            db.session.add(emp)
            next_num += 1
            count += 1
        db.session.commit()
        flash(f"Successfully imported {count} employees.", "success")
        return redirect(url_for("employees.list_employees"))

    return render_template("upload.html", upload_type="Employee Data",
                            columns=["name", "email", "phone", "gender", "age", "designation", "salary", "department", "status"])
