import sys
import os

# Add project root and backend dir to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
for p in (PROJECT_ROOT, BACKEND_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.employee import Employee
from app.models.department import Department
from datetime import date

app = create_app()

with app.app_context():
    # 1. Print all existing users
    users = User.query.all()
    print("=== Current Users in Database ===")
    for u in users:
        print(f"ID: {u.id} | Username: {u.username} | Email: {u.email} | Role: {u.role} | Active: {u.is_active_account}")

    # 2. Reset or Create 'admin' user
    admin_user = User.query.filter((User.username == "admin") | (User.email == "admin@company.com")).first()
    if not admin_user:
        print("\nCreating new admin user: admin ...")
        admin_user = User(
            username="admin",
            email="admin@company.com",
            role="admin",
            is_active_account=True
        )
        admin_user.set_password("Admin@123")
        db.session.add(admin_user)
        db.session.commit()
    else:
        print("\nUpdating existing admin user password to Admin@123 and setting active...")
        admin_user.username = "admin"
        admin_user.email = "admin@company.com"
        admin_user.role = "admin"
        admin_user.is_active_account = True
        admin_user.set_password("Admin@123")
        db.session.commit()

    # Ensure admin has an Employee record
    admin_emp = Employee.query.filter_by(user_id=admin_user.id).first()
    if not admin_emp:
        dept = Department.query.first()
        if not dept:
            dept = Department(name="Operations", description="Operations department")
            db.session.add(dept)
            db.session.commit()

        admin_emp = Employee(
            employee_code="EMP-0001",
            user_id=admin_user.id,
            name="System Administrator",
            email="admin@company.com",
            phone="9000000001",
            gender="Other",
            age=35,
            designation="System Administrator",
            salary=120000,
            joining_date=date(2020, 1, 1),
            address="Headquarters",
            experience_years=10.0,
            education="Master",
            status="Active",
            department_id=dept.id,
        )
        db.session.add(admin_emp)
        db.session.commit()
        print("Created associated Employee record for admin.")
    else:
        admin_emp.status = "Active"
        db.session.commit()
        print("Updated associated Employee record for admin.")

    # Also reset or create a manager account
    mgr_user = User.query.filter_by(username="manager").first()
    if not mgr_user:
        mgr_user = User(
            username="manager",
            email="manager@company.com",
            role="manager",
            is_active_account=True
        )
        mgr_user.set_password("Manager@123")
        db.session.add(mgr_user)
        db.session.commit()
        print("Created manager account: manager / Manager@123")
    else:
        mgr_user.is_active_account = True
        mgr_user.set_password("Manager@123")
        db.session.commit()
        print("Updated manager password to Manager@123")

    # If user 'utk' exists, let's also set its password to Admin@123 and activate it
    utk_user = User.query.filter((User.username == "utk") | (User.email == "utkarshbelsare488@gmail.com")).first()
    if utk_user:
        utk_user.set_password("Admin@123")
        utk_user.is_active_account = True
        db.session.commit()
        print("Reset password for user 'utk' to Admin@123 and activated account.")

    print("\nSUCCESS: All admin and manager accounts configured.")
