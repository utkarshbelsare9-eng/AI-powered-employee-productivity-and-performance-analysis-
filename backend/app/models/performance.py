from datetime import datetime
from app.models import db


class Performance(db.Model):
    """Monthly aggregated performance / productivity metrics per employee."""

    __tablename__ = "performance"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    month = db.Column(db.String(7), nullable=False)  # 'YYYY-MM'

    attendance_percent = db.Column(db.Float, default=0)
    task_completion_rate = db.Column(db.Float, default=0)
    work_efficiency = db.Column(db.Float, default=0)
    time_management_score = db.Column(db.Float, default=0)
    overtime_score = db.Column(db.Float, default=0)
    punctuality_score = db.Column(db.Float, default=0)
    consistency_score = db.Column(db.Float, default=0)

    manager_rating = db.Column(db.Float, default=0)   # 1-5
    customer_rating = db.Column(db.Float, default=0)  # 1-5
    skill_score = db.Column(db.Float, default=0)       # 0-100

    productivity_score = db.Column(db.Float, default=0)  # 0-100 composite
    performance_score = db.Column(db.Float, default=0)    # 0-100 composite
    performance_grade = db.Column(db.String(20))           # Excellent/Good/Average/Poor
    risk_score = db.Column(db.Float, default=0)            # 0-100 attrition/burnout risk

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("employee_id", "month", name="uq_emp_month"),)

    def __repr__(self):
        return f"<Performance emp={self.employee_id} {self.month} {self.performance_grade}>"
