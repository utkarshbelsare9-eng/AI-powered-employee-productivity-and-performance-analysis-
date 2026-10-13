from datetime import datetime
from app.models import db


class ActivityAgentToken(db.Model):
    """Authentication token for the employee's local activity collector.

    Tokens authorize only activity ingestion for the linked employee.
    The token is stored as a hash; the plaintext token is shown only when
    generated/regenerated in the employee's authenticated web session.
    """

    __tablename__ = "activity_agent_tokens"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False, unique=True, index=True)
    token_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_used_at = db.Column(db.DateTime)

    employee = db.relationship("Employee", backref=db.backref("activity_agent_token", uselist=False))
