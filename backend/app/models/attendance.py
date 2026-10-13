from datetime import datetime
from app.models import db


class Attendance(db.Model):
    __tablename__ = "attendance"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # Present/Absent/Leave/WFH
    check_in = db.Column(db.Time)
    check_out = db.Column(db.Time)
    working_hours = db.Column(db.Float, default=0)
    overtime_hours = db.Column(db.Float, default=0)
    late_entry = db.Column(db.Boolean, default=False)
    early_exit = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("employee_id", "date", name="uq_emp_date"),)

    def __repr__(self):
        return f"<Attendance emp={self.employee_id} {self.date} {self.status}>"
