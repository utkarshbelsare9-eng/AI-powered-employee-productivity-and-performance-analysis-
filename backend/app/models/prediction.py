from datetime import datetime
from app.models import db


class Prediction(db.Model):
    """Stores ML model output for an employee at a point in time."""

    __tablename__ = "predictions"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False)
    predicted_grade = db.Column(db.String(20))  # Excellent/Good/Average/Poor
    confidence = db.Column(db.Float)             # 0-100
    probabilities = db.Column(db.Text)            # JSON string of class probabilities
    risk_level = db.Column(db.String(20))          # Low/Medium/High
    attrition_risk_percent = db.Column(db.Float, default=0)
    burnout_risk_percent = db.Column(db.Float, default=0)
    promotion_eligible = db.Column(db.Boolean, default=False)
    recommendations = db.Column(db.Text)  # JSON list of recommendation strings
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Prediction emp={self.employee_id} {self.predicted_grade}>"
