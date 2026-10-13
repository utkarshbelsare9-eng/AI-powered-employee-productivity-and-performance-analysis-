from datetime import datetime
from app.models import db


class Employee(db.Model):
    __tablename__ = "employees"

    id = db.Column(db.Integer, primary_key=True)
    employee_code = db.Column(db.String(20), unique=True, nullable=False)  # e.g. EMP-0001
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    gender = db.Column(db.String(10))
    age = db.Column(db.Integer)
    designation = db.Column(db.String(100))
    salary = db.Column(db.Float)
    joining_date = db.Column(db.Date)
    address = db.Column(db.String(255))
    experience_years = db.Column(db.Float, default=0)
    education = db.Column(db.String(150))
    status = db.Column(db.String(20), default="Active")  # Active/Inactive/On Leave

    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"))
    manager_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Self-referential manager relationship
    manager = db.relationship("Employee", remote_side=[id], backref="team_members")

    attendances = db.relationship("Attendance", backref="employee", lazy=True, cascade="all, delete-orphan")
    tasks = db.relationship("Task", backref="employee", lazy=True, cascade="all, delete-orphan")
    performances = db.relationship("Performance", backref="employee", lazy=True, cascade="all, delete-orphan")
    predictions = db.relationship("Prediction", backref="employee", lazy=True, cascade="all, delete-orphan")
    leaves = db.relationship(
        "Leave",
        foreign_keys="Leave.employee_id",
        backref="employee",
        lazy=True,
        cascade="all, delete-orphan",
    )
    skills = db.relationship("Skill", backref="employee", lazy=True, cascade="all, delete-orphan")
    achievements = db.relationship("Achievement", backref="employee", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Employee {self.employee_code} {self.name}>"
