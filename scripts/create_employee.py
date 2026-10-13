import sys
import os

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
    # Check if emp1 exists
    emp_user = User.query.filter_by(username="emp1").first()
    if not emp_user:
        emp_user = User(
            username="emp1",
            email="emp1@company.com",
            role="employee",
            is_active_account=True
        )
        emp_user.set_password("Employee@123")
        db.session.add(emp_user)
        db.session.commit()

        dept = Department.query.first()
        emp = Employee(
            employee_code="EMP-0002",
            user_id=emp_user.id,
            name="John Doe",
            email="emp1@company.com",
            phone="9000000002",
            gender="Male",
            age=28,
            designation="Software Engineer",
            salary=65000,
            joining_date=date(2022, 5, 10),
            address="Tech Park",
            experience_years=3.5,
            education="B.Tech",
            status="Active",
            department_id=dept.id if dept else None,
        )
        db.session.add(emp)
        db.session.commit()
        print("Created employee: emp1 / Employee@123")
    else:
        emp_user.set_password("Employee@123")
        emp_user.is_active_account = True
        db.session.commit()
        print("Updated employee: emp1 / Employee@123")

    print("\nAll accounts in DB:")
    for u in User.query.all():
        print(f"Username: {u.username} | Role: {u.role} | Active: {u.is_active_account}")
