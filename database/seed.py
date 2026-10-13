"""
Seeds the database with realistic sample data:
departments, users (admin/managers/employees), attendance history,
tasks, monthly performance records, and AI predictions.

Run with:  python database/seed.py
(Also auto-invoked by app.py on first run if the DB is empty.)
"""
import os
import sys
import random
from datetime import date, timedelta, datetime, time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
for p in (PROJECT_ROOT, BACKEND_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.department import Department
from app.models.employee import Employee
from app.models.attendance import Attendance
from app.models.task import Task
from app.models.performance import Performance
from app.models.prediction import Prediction
from app.models.leave import Leave
from app.models.skill import Skill
from app.models.achievement import Achievement
from app.models.notification import Notification
from app.utils.helpers import compute_productivity_metrics, score_to_grade
from app.machine_learning.predict import predict_employee

random.seed(7)

DEPARTMENTS = ["Engineering", "Human Resources", "Sales", "Marketing", "Finance", "Customer Support", "Operations"]
DESIGNATIONS = {
    "Engineering": ["Software Engineer", "Senior Engineer", "QA Engineer", "DevOps Engineer", "Tech Lead"],
    "Human Resources": ["HR Executive", "HR Manager", "Talent Acquisition Specialist"],
    "Sales": ["Sales Executive", "Sales Manager", "Account Manager"],
    "Marketing": ["Marketing Executive", "SEO Specialist", "Content Strategist"],
    "Finance": ["Accountant", "Financial Analyst", "Finance Manager"],
    "Customer Support": ["Support Executive", "Support Team Lead"],
    "Operations": ["Operations Executive", "Operations Manager"],
}
SKILLS_POOL = ["Python", "SQL", "Communication", "Leadership", "Excel", "Project Management",
               "Negotiation", "Data Analysis", "Cloud (AWS)", "Customer Service", "Java", "React"]
FIRST_NAMES = ["Aarav", "Vivaan", "Aditya", "Isha", "Ananya", "Priya", "Rohan", "Kabir", "Neha", "Sara",
               "Arjun", "Meera", "Kiran", "Rahul", "Simran", "Ravi", "Pooja", "Aman", "Divya", "Karan",
               "Nisha", "Manish", "Sneha", "Vikram", "Tanvi", "Yash", "Ritu", "Sandeep", "Anjali", "Deepak"]
LAST_NAMES = ["Sharma", "Verma", "Iyer", "Kapoor", "Reddy", "Nair", "Gupta", "Mehta", "Joshi", "Rao",
              "Chopra", "Malhotra", "Bose", "Pillai", "Agarwal", "Desai", "Bhat", "Singh", "Kulkarni", "Menon"]


def rand_name(used):
    while True:
        n = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        if n not in used:
            used.add(n)
            return n


def seed():
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()

        # ---- Departments ----
        dept_objs = {}
        for d in DEPARTMENTS:
            dep = Department(name=d, description=f"{d} department")
            db.session.add(dep)
            dept_objs[d] = dep
        db.session.commit()

        used_names = set()

        # ---- Admin ----
        admin_user = User(username="admin", email="admin@company.com", role="admin")
        admin_user.set_password("Admin@123")
        db.session.add(admin_user)
        db.session.commit()

        admin_emp = Employee(
            employee_code="EMP-0001", user_id=admin_user.id, name="System Administrator",
            email="admin@company.com", phone="9000000001", gender="Other", age=34,
            designation="System Administrator", salary=120000, joining_date=date(2020, 1, 5),
            address="HQ Building, Pune", experience_years=8, education="M.Tech",
            status="Active", department_id=dept_objs["Operations"].id,
        )
        db.session.add(admin_emp)
        db.session.commit()

        # ---- Managers (1 per department) ----
        managers = {}
        code_counter = 2
        for dname, dep in dept_objs.items():
            uname = f"manager.{dname.lower().replace(' ', '')}"
            mgr_user = User(username=uname, email=f"{uname}@company.com", role="manager")
            mgr_user.set_password("Manager@123")
            db.session.add(mgr_user)
            db.session.commit()

            name = rand_name(used_names)
            mgr_emp = Employee(
                employee_code=f"EMP-{code_counter:04d}", user_id=mgr_user.id, name=name,
                email=f"{uname}@company.com", phone=f"90000{code_counter:05d}",
                gender=random.choice(["Male", "Female"]), age=random.randint(32, 46),
                designation=f"{dname} Manager", salary=random.randint(85000, 140000),
                joining_date=date(2018, random.randint(1, 12), random.randint(1, 28)),
                address="Pune, Maharashtra", experience_years=round(random.uniform(6, 15), 1),
                education=random.choice(["MBA", "M.Tech", "B.Tech", "M.Com"]),
                status="Active", department_id=dep.id,
            )
            db.session.add(mgr_emp)
            db.session.commit()
            managers[dname] = mgr_emp
            code_counter += 1

        # ---- Employees ----
        employees = []
        n_employees = 45
        for i in range(n_employees):
            dname = random.choice(DEPARTMENTS)
            dep = dept_objs[dname]
            mgr = managers[dname]
            name = rand_name(used_names)
            uname = f"emp{code_counter}"
            emp_user = User(username=uname, email=f"{uname}@company.com", role="employee")
            emp_user.set_password("Employee@123")
            db.session.add(emp_user)
            db.session.commit()

            emp = Employee(
                employee_code=f"EMP-{code_counter:04d}", user_id=emp_user.id, name=name,
                email=f"{uname}@company.com", phone=f"90000{code_counter:05d}",
                gender=random.choice(["Male", "Female"]), age=random.randint(22, 55),
                designation=random.choice(DESIGNATIONS[dname]),
                salary=random.randint(35000, 95000),
                joining_date=date(random.randint(2016, 2024), random.randint(1, 12), random.randint(1, 28)),
                address=random.choice(["Pimpri, Pune", "Mumbai", "Bangalore", "Hyderabad", "Nagpur", "Nashik"]),
                experience_years=round(random.uniform(0.5, 18), 1),
                education=random.choice(["B.Tech", "B.Com", "MBA", "M.Sc", "BCA", "MCA"]),
                status=random.choices(["Active", "On Leave", "Inactive"], weights=[90, 7, 3])[0],
                department_id=dep.id, manager_id=mgr.id,
            )
            db.session.add(emp)
            db.session.commit()
            employees.append(emp)

            # Skills
            for s in random.sample(SKILLS_POOL, k=random.randint(3, 5)):
                db.session.add(Skill(employee_id=emp.id, name=s, proficiency=random.randint(40, 98)))

            code_counter += 1
        db.session.commit()

        all_staff = [admin_emp] + list(managers.values()) + employees

        # ---- Attendance (last 90 days) + Tasks + Monthly Performance ----
        today = date.today()
        start_day = today - timedelta(days=90)

        for emp in employees + list(managers.values()):
            # Attendance
            d = start_day
            working_days = 0
            present_days = 0
            late_count = 0
            total_hours = 0
            total_ot = 0
            base_reliability = random.uniform(0.75, 0.98)  # per-employee tendency

            while d <= today:
                if d.weekday() < 5:  # Mon-Fri
                    working_days += 1
                    roll = random.random()
                    if roll < base_reliability:
                        status = "Present"
                    elif roll < base_reliability + 0.06:
                        status = "Work From Home"
                    elif roll < base_reliability + 0.11:
                        status = "Leave"
                    else:
                        status = "Absent"

                    late = False
                    early = False
                    hours = 0
                    ot = 0
                    check_in = check_out = None
                    if status in ("Present", "Work From Home"):
                        present_days += 1
                        start_hour = random.choice([9, 9, 9, 10])
                        start_min = random.randint(0, 59)
                        late = (start_hour > 9) or (start_hour == 9 and start_min > 15)
                        if late:
                            late_count += 1
                        check_in = time(start_hour, start_min)
                        work_len = round(random.uniform(6.5, 10.5), 1)
                        hours = work_len
                        ot = max(0, work_len - 8)
                        end_hour = min(23, start_hour + int(work_len))
                        check_out = time(end_hour % 24, random.randint(0, 59))
                        early = work_len < 7
                        total_hours += hours
                        total_ot += ot

                    db.session.add(Attendance(
                        employee_id=emp.id, date=d, status=status,
                        check_in=check_in, check_out=check_out,
                        working_hours=hours, overtime_hours=round(ot, 1),
                        late_entry=late, early_exit=early,
                    ))
                d += timedelta(days=1)

            attendance_percent = round((present_days / working_days) * 100, 1) if working_days else 0
            avg_hours = round(total_hours / present_days, 1) if present_days else 0

            # Tasks (last 60 days)
            n_tasks = random.randint(15, 35)
            completed = 0
            missed = 0
            total_est = 0
            total_act = 0
            categories = ["Development", "Design", "Documentation", "Client Meeting", "Testing", "Support", "Research"]
            for t in range(n_tasks):
                assigned_date = today - timedelta(days=random.randint(0, 60))
                est_hours = round(random.uniform(2, 20), 1)
                deadline = assigned_date + timedelta(days=random.randint(2, 14))
                status_roll = random.random()
                priority = random.choice(["Low", "Medium", "High", "Critical"])
                if status_roll < base_reliability - 0.05:
                    status = "Completed"
                    completion_date = deadline + timedelta(days=random.choice([-3, -2, -1, 0, 0, 1, 2]))
                    act_hours = round(est_hours * random.uniform(0.8, 1.4), 1)
                    pct = 100
                    completed += 1
                    if completion_date > deadline:
                        missed += 1
                elif status_roll < base_reliability + 0.05:
                    status = "In Progress"
                    completion_date = None
                    act_hours = round(est_hours * random.uniform(0.3, 0.8), 1)
                    pct = random.randint(20, 80)
                else:
                    status = random.choice(["Pending", "Delayed"])
                    completion_date = None
                    act_hours = 0
                    pct = random.randint(0, 20)
                    if status == "Delayed":
                        missed += 1

                total_est += est_hours
                total_act += act_hours

                db.session.add(Task(
                    employee_id=emp.id, title=f"{random.choice(categories)} Task #{t+1}",
                    category=random.choice(categories), priority=priority, status=status,
                    completed_percent=pct, estimated_hours=est_hours, actual_hours=act_hours,
                    assigned_date=assigned_date, deadline=deadline, completion_date=completion_date,
                ))

            task_completion_rate = round((completed / n_tasks) * 100, 1) if n_tasks else 0
            manager_rating = round(random.uniform(2.5, 5.0), 1)
            customer_rating = round(random.uniform(2.5, 5.0), 1)
            skill_score = round(random.uniform(45, 98), 1)

            metrics = compute_productivity_metrics(
                attendance_percent, task_completion_rate, total_ot, late_count,
                working_days, manager_rating, customer_rating
            )
            grade = score_to_grade(metrics["performance_score"])

            month_str = today.strftime("%Y-%m")
            perf = Performance(
                employee_id=emp.id, month=month_str,
                attendance_percent=attendance_percent,
                task_completion_rate=task_completion_rate,
                work_efficiency=metrics["work_efficiency"],
                time_management_score=metrics["time_management_score"],
                overtime_score=metrics["overtime_score"],
                punctuality_score=metrics["punctuality_score"],
                consistency_score=metrics["consistency_score"],
                manager_rating=manager_rating, customer_rating=customer_rating,
                skill_score=skill_score,
                productivity_score=metrics["productivity_score"],
                performance_score=metrics["performance_score"],
                performance_grade=grade,
                risk_score=round(max(0, 100 - metrics["performance_score"] - random.uniform(-5, 5)), 1),
            )
            db.session.add(perf)

            # AI Prediction using the trained model
            try:
                pred = predict_employee({
                    "attendance_percent": attendance_percent,
                    "avg_working_hours": avg_hours,
                    "late_entries": late_count,
                    "leave_days": working_days - present_days,
                    "tasks_assigned": n_tasks,
                    "tasks_completed": completed,
                    "deadlines_missed": missed,
                    "overtime_hours": total_ot,
                    "customer_rating": customer_rating,
                    "manager_rating": manager_rating,
                    "skill_score": skill_score,
                    "experience_years": emp.experience_years or 0,
                })
                import json as _json
                db.session.add(Prediction(
                    employee_id=emp.id, predicted_grade=pred["grade"], confidence=pred["confidence"],
                    probabilities=_json.dumps(pred["probabilities"]), risk_level=pred["risk_level"],
                    attrition_risk_percent=pred["attrition_risk_percent"],
                    burnout_risk_percent=pred["burnout_risk_percent"],
                    promotion_eligible=pred["promotion_eligible"],
                    recommendations=_json.dumps(pred["recommendations"]),
                ))
            except Exception as e:
                print(f"[WARN] prediction failed for {emp.name}: {e}")

            # Achievements (random, for higher performers)
            if grade in ("Excellent", "Good") and random.random() < 0.4:
                db.session.add(Achievement(
                    employee_id=emp.id,
                    title=random.choice(["Employee of the Month", "Top Performer Q2", "Perfect Attendance Award",
                                          "Client Appreciation Award", "Innovation Award"]),
                    description="Recognized for outstanding contribution.",
                    date_awarded=today - timedelta(days=random.randint(5, 200)),
                    icon=random.choice(["fa-trophy", "fa-medal", "fa-star", "fa-award"]),
                ))

            # Leave requests
            for _ in range(random.randint(0, 2)):
                ls = today - timedelta(days=random.randint(1, 60))
                db.session.add(Leave(
                    employee_id=emp.id, start_date=ls, end_date=ls + timedelta(days=random.randint(1, 3)),
                    reason=random.choice(["Personal", "Medical", "Family Function", "Vacation"]),
                    status=random.choice(["Pending", "Approved", "Approved", "Rejected"]),
                ))

            # Notifications
            if attendance_percent < 80:
                db.session.add(Notification(
                    user_id=emp.user_id, title="Low Attendance Alert",
                    message=f"Your attendance is {attendance_percent}% this period. Please improve consistency.",
                    category="warning",
                ))
            if grade == "Poor":
                db.session.add(Notification(
                    user_id=emp.user_id, title="Performance Review Needed",
                    message="Your recent performance score needs attention. Speak with your manager.",
                    category="danger",
                ))

        db.session.commit()
        print(f"[SUCCESS] Seeded {len(employees)} employees, {len(managers)} managers, 1 admin.")
        print("Login credentials:")
        print("  Admin    -> username: admin            password: Admin@123")
        print("  Manager  -> username: manager.engineering  password: Manager@123")
        print("  Employee -> username: emp2..emp{}  password: Employee@123".format(code_counter - 1))


if __name__ == "__main__":
    seed()
