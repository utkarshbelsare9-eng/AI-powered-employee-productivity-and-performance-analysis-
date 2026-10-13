from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
from app.extensions import db
from app.models.activity import ActivityLog
from app.models.activity_token import ActivityAgentToken
from app.models.employee import Employee
from app.api.auth_middleware import jwt_required

activity_api_bp = Blueprint("api_activity", __name__, url_prefix="/activity")


@activity_api_bp.route("/agent/ping", methods=["POST"])
def agent_ping():
    """Desktop activity agent endpoint for uploading 60-second activity telemetry."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"success": False, "error": "Token required"}), 401

    raw_token = auth_header.split(" ", 1)[1].strip()
    token_record = ActivityAgentToken.verify_token(raw_token)
    if not token_record:
        return jsonify({"success": False, "error": "Invalid or revoked agent token"}), 401

    data = request.get_json(silent=True) or {}
    employee_id = token_record.employee_id

    # Aggregate transparent telemetry only (No keystroke identities or typed text)
    log_entry = ActivityLog(
        employee_id=employee_id,
        timestamp=datetime.now(timezone.utc),
        keyboard_events=int(data.get("keyboard_events", 0)),
        mouse_moves=int(data.get("mouse_moves", 0)),
        mouse_clicks=int(data.get("mouse_clicks", 0)),
        scroll_events=int(data.get("scroll_events", 0)),
        idle_seconds=float(data.get("idle_seconds", 0.0)),
        active_application=str(data.get("active_application", "Unknown"))[:120],
        source="desktop_agent"
    )
    db.session.add(log_entry)
    db.session.commit()

    return jsonify({"success": True, "message": "Telemetry received"}), 200


@activity_api_bp.route("/summary/<int:emp_id>", methods=["GET"])
@jwt_required
def get_activity_summary(emp_id):
    """Retrieve activity tracking summary for an employee."""
    user = request.current_jwt_user
    if user.role == "employee" and user.employee and user.employee.id != emp_id:
        return jsonify({"success": False, "error": "Access denied"}), 403

    logs = ActivityLog.query.filter_by(employee_id=emp_id).order_by(ActivityLog.timestamp.desc()).limit(60).all()
    
    total_keys = sum(l.keyboard_events for l in logs)
    total_clicks = sum(l.mouse_clicks for l in logs)
    avg_idle = sum(l.idle_seconds for l in logs) / max(len(logs), 1)

    return jsonify({
        "success": True,
        "employee_id": emp_id,
        "intervals_recorded": len(logs),
        "total_keyboard_events": total_keys,
        "total_mouse_clicks": total_clicks,
        "avg_idle_seconds_per_interval": round(avg_idle, 1)
    }), 200
