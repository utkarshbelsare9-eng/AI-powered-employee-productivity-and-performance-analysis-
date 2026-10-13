from datetime import datetime
from app.models import db


class ActivityLog(db.Model):
    """One row per tracking interval (default: 60 seconds) for an employee.

    The browser-side tracker (static/js/activity_tracker.js) watches for
    mouse and keyboard events while the app is open. Every interval it
    reports whether *any* mouse activity and/or *any* keyboard activity
    happened, and this row is stored. Daily totals are derived by summing
    intervals where mouse_active or keyboard_active is true.
    """

    __tablename__ = "activity_logs"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey("employees.id"), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    mouse_active = db.Column(db.Boolean, default=False)
    keyboard_active = db.Column(db.Boolean, default=False)

    mouse_events = db.Column(db.Integer, default=0)     # total mouse events in interval
    keyboard_events = db.Column(db.Integer, default=0)  # total key presses; NEVER stores key values
    mouse_clicks = db.Column(db.Integer, default=0)
    mouse_moves = db.Column(db.Integer, default=0)
    scroll_events = db.Column(db.Integer, default=0)
    idle_seconds = db.Column(db.Integer, default=0)
    active_application = db.Column(db.String(120), default=None)  # app/process name only, no window title
    interval_seconds = db.Column(db.Integer, default=60)

    source = db.Column(db.String(20), default="browser")  # browser / desktop_agent

    employee = db.relationship("Employee", backref=db.backref(
        "activity_logs", lazy=True, cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<ActivityLog emp={self.employee_id} {self.timestamp} m={self.mouse_active} k={self.keyboard_active}>"
