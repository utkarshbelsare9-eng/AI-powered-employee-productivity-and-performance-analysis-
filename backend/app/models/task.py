from datetime import datetime
from app.models import db


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100))
    priority = db.Column(db.String(20), default="Medium")  # Low/Medium/High/Critical
    status = db.Column(db.String(20), default="Pending")   # Pending/In Progress/Completed/Delayed
    completed_percent = db.Column(db.Integer, default=0)
    estimated_hours = db.Column(db.Float, default=0)
    actual_hours = db.Column(db.Float, default=0)
    assigned_date = db.Column(db.Date, default=datetime.utcnow)
    deadline = db.Column(db.Date)
    completion_date = db.Column(db.Date)

    @property
    def is_delayed(self):
        if self.status == "Completed" and self.completion_date and self.deadline:
            return self.completion_date > self.deadline
        if self.status != "Completed" and self.deadline:
            from datetime import date
            return date.today() > self.deadline
        return False

    def __repr__(self):
        return f"<Task {self.title} ({self.status})>"
