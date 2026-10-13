from datetime import date, datetime
import hashlib
import secrets

from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from flask_login import login_required, current_user

from app.models import db
from app.models.activity import ActivityLog
from app.models.activity_token import ActivityAgentToken
from app.models.attendance import Attendance

activity_bp = Blueprint("activity", __name__, url_prefix="/api/activity")

PING_INTERVAL_SECONDS = 60


def _hash_token(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _employee_authorized(employee_id):
    if current_user.is_admin:
        return True
    if current_user.is_manager:
        from app.models.employee import Employee
        emp = Employee.query.get(employee_id)
        return bool(emp and emp.manager_id == getattr(current_user.employee, "id", None))
    return bool(current_user.employee and current_user.employee.id == employee_id)


def _active_hours_for(employee_id, day):
    rows = ActivityLog.query.filter_by(employee_id=employee_id, date=day).all()
    mouse_h = sum(1 for r in rows if r.mouse_active) * PING_INTERVAL_SECONDS / 3600.0
    keyboard_h = sum(1 for r in rows if r.keyboard_active) * PING_INTERVAL_SECONDS / 3600.0
    combined_h = sum(1 for r in rows if r.mouse_active or r.keyboard_active) * PING_INTERVAL_SECONDS / 3600.0
    return round(mouse_h, 2), round(keyboard_h, 2), round(combined_h, 2)


def _sync_attendance_working_hours(employee_id, day, total_hours):
    rec = Attendance.query.filter_by(employee_id=employee_id, date=day).first()
    if not rec:
        rec = Attendance(employee_id=employee_id, date=day, status="Present")
        db.session.add(rec)
    rec.working_hours = total_hours
    if rec.status not in ("Present", "Work From Home"):
        rec.status = "Present"


def _daily_metrics(employee_id, day):
    logs = ActivityLog.query.filter_by(employee_id=employee_id, date=day).order_by(ActivityLog.timestamp).all()
    interval_h = PING_INTERVAL_SECONDS / 3600.0
    mouse_h, keyboard_h, computer_h = _active_hours_for(employee_id, day)
    productive_h = round(sum(1 for l in logs if l.keyboard_active) * interval_h, 2)

    if logs:
        # Only activity intervals are counted; long gaps are not automatically treated as work.
        all_activities_h = round(sum((l.interval_seconds or PING_INTERVAL_SECONDS)
                                     for l in logs if l.mouse_active or l.keyboard_active) / 3600.0, 2)
    else:
        all_activities_h = 0.0

    att = Attendance.query.filter_by(employee_id=employee_id, date=day).first()
    office_h = None
    check_in = att.check_in if att else None
    check_out = att.check_out if att else None
    if check_in and check_out:
        t1 = datetime.combine(day, check_in)
        t2 = datetime.combine(day, check_out)
        office_h = round((t2 - t1).total_seconds() / 3600.0, 2)

    total_events = sum((l.mouse_events or 0) + (l.keyboard_events or 0) for l in logs)
    total_clicks = sum(l.mouse_clicks or 0 for l in logs)
    total_moves = sum(l.mouse_moves or 0 for l in logs)
    total_scrolls = sum(l.scroll_events or 0 for l in logs)
    total_idle = sum(l.idle_seconds or 0 for l in logs)

    return {
        "date": day,
        "check_in": check_in,
        "check_out": check_out,
        "office_hours": office_h,
        "all_activities_hours": all_activities_h,
        "computer_activities_hours": computer_h,
        "productive_hours": productive_h,
        "keyboard_events": sum(l.keyboard_events or 0 for l in logs),
        "mouse_events": sum(l.mouse_events or 0 for l in logs),
        "mouse_clicks": total_clicks,
        "mouse_moves": total_moves,
        "scroll_events": total_scrolls,
        "idle_seconds": total_idle,
        "total_events": total_events,
        "has_data": bool(logs) or att is not None,
    }


def build_timesheet_rows(employee_id, num_days=7):
    from datetime import timedelta
    today = date.today()
    return [_daily_metrics(employee_id, today - timedelta(days=i)) for i in range(num_days)]


def build_timeline_blocks(employee_id, day):
    logs = ActivityLog.query.filter_by(employee_id=employee_id, date=day).order_by(ActivityLog.timestamp).all()
    blocks = []
    for l in logs:
        minute = l.timestamp.hour * 60 + l.timestamp.minute
        if l.keyboard_active:
            state = "productive"
        elif l.mouse_active:
            state = "active"
        else:
            state = "idle"
        if blocks and blocks[-1]["state"] == state and minute - blocks[-1]["end"] <= 1:
            blocks[-1]["end"] = minute + 1
        else:
            blocks.append({"start": minute, "end": minute + 1, "state": state})
    return blocks


@activity_bp.route("/timeline/<int:employee_id>")
@login_required
def timeline(employee_id):
    if not _employee_authorized(employee_id):
        return jsonify({"error": "Not authorized."}), 403

    day_str = request.args.get("date")
    try:
        day = datetime.strptime(day_str, "%Y-%m-%d").date() if day_str else date.today()
    except ValueError:
        return jsonify({"error": "Invalid date."}), 400

    blocks = build_timeline_blocks(employee_id, day)
    metrics = _daily_metrics(employee_id, day)
    return jsonify({
        "date": day.isoformat(),
        "blocks": blocks,
        "check_in": metrics["check_in"].strftime("%H:%M") if metrics["check_in"] else None,
        "check_out": metrics["check_out"].strftime("%H:%M") if metrics["check_out"] else None,
        "office_hours": metrics["office_hours"],
        "all_activities_hours": metrics["all_activities_hours"],
        "computer_activities_hours": metrics["computer_activities_hours"],
        "productive_hours": metrics["productive_hours"],
        "keyboard_events": metrics["keyboard_events"],
        "mouse_events": metrics["mouse_events"],
        "mouse_clicks": metrics["mouse_clicks"],
        "mouse_moves": metrics["mouse_moves"],
        "scroll_events": metrics["scroll_events"],
        "idle_seconds": metrics["idle_seconds"],
    })


def _save_activity(employee_id, data, source):
    """Store aggregate activity only. Never store key names, text, clipboard data or screenshots."""
    mouse_events = max(0, int(data.get("mouse_events") or 0))
    keyboard_events = max(0, int(data.get("keyboard_events") or 0))
    mouse_clicks = max(0, int(data.get("mouse_clicks") or 0))
    mouse_moves = max(0, int(data.get("mouse_moves") or 0))
    scroll_events = max(0, int(data.get("scroll_events") or 0))
    idle_seconds = max(0, min(int(data.get("idle_seconds") or 0), PING_INTERVAL_SECONDS))
    interval_seconds = max(1, min(int(data.get("interval_seconds") or PING_INTERVAL_SECONDS), PING_INTERVAL_SECONDS))
    app_name = (str(data.get("active_application") or "")[:120]).strip() or None

    mouse_active = mouse_events > 0 or mouse_clicks > 0 or mouse_moves > 0 or scroll_events > 0
    keyboard_active = keyboard_events > 0

    log = ActivityLog(
        employee_id=employee_id,
        date=date.today(),
        timestamp=datetime.utcnow(),
        mouse_active=mouse_active,
        keyboard_active=keyboard_active,
        mouse_events=mouse_events,
        keyboard_events=keyboard_events,
        mouse_clicks=mouse_clicks,
        mouse_moves=mouse_moves,
        scroll_events=scroll_events,
        idle_seconds=idle_seconds,
        active_application=app_name,
        interval_seconds=interval_seconds,
        source=source,
    )
    db.session.add(log)

    _, _, total_h = _active_hours_for(employee_id, date.today())
    if mouse_active or keyboard_active:
        total_h = round(total_h + interval_seconds / 3600.0, 2)
    _sync_attendance_working_hours(employee_id, date.today(), total_h)
    db.session.commit()

    return {
        "ok": True,
        "date": date.today().isoformat(),
        "mouse_hours": _active_hours_for(employee_id, date.today())[0],
        "keyboard_hours": _active_hours_for(employee_id, date.today())[1],
        "total_active_hours": total_h,
    }


@activity_bp.route("/ping", methods=["POST"])
@login_required
def ping():
    if not current_user.employee:
        return jsonify({"error": "No employee profile linked to this account."}), 400
    return jsonify(_save_activity(current_user.employee.id, request.get_json(silent=True) or {}, "browser"))


@activity_bp.route("/agent/ping", methods=["POST"])
def agent_ping():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return jsonify({"error": "Bearer activity-agent token required."}), 401
    token = auth[7:].strip()
    if len(token) < 20:
        return jsonify({"error": "Invalid activity-agent token."}), 401

    rec = ActivityAgentToken.query.filter_by(token_hash=_hash_token(token)).first()
    if not rec:
        return jsonify({"error": "Invalid activity-agent token."}), 401

    rec.last_used_at = datetime.utcnow()
    result = _save_activity(rec.employee_id, request.get_json(silent=True) or {}, "desktop_agent")
    return jsonify(result)


@activity_bp.route("/agent/token", methods=["POST"])
@login_required
def generate_agent_token():
    if not current_user.employee:
        return jsonify({"error": "No employee profile linked to this account."}), 400

    token = secrets.token_urlsafe(32)
    rec = ActivityAgentToken.query.filter_by(employee_id=current_user.employee.id).first()
    if not rec:
        rec = ActivityAgentToken(employee_id=current_user.employee.id, token_hash=_hash_token(token))
        db.session.add(rec)
    else:
        rec.token_hash = _hash_token(token)
        rec.created_at = datetime.utcnow()
        rec.last_used_at = None
    db.session.commit()
    return jsonify({"token": token})


@activity_bp.route("/summary")
@login_required
def summary():
    if not current_user.employee:
        return jsonify({"error": "No employee profile linked to this account."}), 400
    today = date.today()
    mouse_h, keyboard_h, total_h = _active_hours_for(current_user.employee.id, today)
    metrics = _daily_metrics(current_user.employee.id, today)
    return jsonify({
        "date": today.isoformat(),
        "mouse_hours": mouse_h,
        "keyboard_hours": keyboard_h,
        "total_active_hours": total_h,
        "mouse_events": metrics["mouse_events"],
        "keyboard_events": metrics["keyboard_events"],
        "mouse_clicks": metrics["mouse_clicks"],
        "mouse_moves": metrics["mouse_moves"],
        "scroll_events": metrics["scroll_events"],
        "idle_seconds": metrics["idle_seconds"],
    })


@activity_bp.route("/summary/<int:employee_id>")
@login_required
def summary_for_employee(employee_id):
    if not _employee_authorized(employee_id):
        return jsonify({"error": "Not authorized."}), 403
    day_str = request.args.get("date")
    try:
        day = datetime.strptime(day_str, "%Y-%m-%d").date() if day_str else date.today()
    except ValueError:
        return jsonify({"error": "Invalid date."}), 400
    metrics = _daily_metrics(employee_id, day)
    return jsonify({
        "date": day.isoformat(),
        "mouse_hours": metrics["mouse_hours"] if "mouse_hours" in metrics else _active_hours_for(employee_id, day)[0],
        "keyboard_hours": metrics["keyboard_hours"] if "keyboard_hours" in metrics else _active_hours_for(employee_id, day)[1],
        "total_active_hours": _active_hours_for(employee_id, day)[2],
        "mouse_events": metrics["mouse_events"],
        "keyboard_events": metrics["keyboard_events"],
        "mouse_clicks": metrics["mouse_clicks"],
        "mouse_moves": metrics["mouse_moves"],
        "scroll_events": metrics["scroll_events"],
        "idle_seconds": metrics["idle_seconds"],
    })


@activity_bp.route("/agent/setup")
@login_required
def agent_setup():
    if not current_user.employee:
        flash("No employee profile linked to this account.", "warning")
        return redirect(url_for("dashboard.index"))
    return render_template("activity_agent.html")
