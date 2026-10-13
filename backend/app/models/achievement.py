from datetime import datetime
from app.models import db


class Achievement(db.Model):
    __tablename__ = "achievements"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(255))
    date_awarded = db.Column(db.Date, default=datetime.utcnow)
    icon = db.Column(db.String(50), default="fa-trophy")

    def __repr__(self):
        return f"<Achievement {self.title}>"
