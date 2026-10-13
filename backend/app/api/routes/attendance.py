from flask import Blueprint, request, jsonify
from datetime import date, datetime
from app.extensions import db
from app.models.attendance import Attendance
from app.models.employee import Employee
from app.api.auth_middleware import jwt_required

attendance_api_bp = Blueprint("api_attendance", __name__, url_prefix="/attendance")


@attendance_api_bp.route("/history", methods=["GET"])
@jwt_required
def get_attendance_history():
    """Retrieve attendance history for employee or team."""
    user = request.current_jwt_user
    emp_id = request.args.get("employee_id", type=int)

    if user.role == "employee":
        if not user.employee:
            return jsonify({"success": False, "error": "No associated employee record"}), 404
        emp_id = user.employee.id
    elif not emp_id and user.employee:
        emp_id = user.employee.id

    query = Attendance.query
    if emp_id:
        query = query.filter_by(employee_id=emp_id)

    records = query.order_by(Attendance.date.desc()).limit(60).all()

    return jsonify({
        "success": True,
        "count": len(records),
        "attendance": [{
            "id": a.id,
            "employee_id": a.employee_id,
            "date": a.date.isoformat(),
            "status": a.status,
            "check_in": a.check_in.strftime("%H:%M:%S") if a.check_in else None,
            "check_out": a.check_out.strftime("%H:%M:%S") if a.check_out else None,
            "working_hours": a.working_hours,
            "overtime_hours": a.overtime_hours,
            "is_late": a.is_late
        } for a in records]
    }), 200


@attendance_api_bp.route("/check-in", methods=["POST"])
@jwt_required
def api_check_in():
    """Mobile / Web clock-in for the authenticated employee."""
    user = request.current_jwt_user
    if not user.employee:
        return jsonify({"success": False, "error": "No employee profile found"}), 404

    today = date.today()
    record = Attendance.query.filter_by(employee_id=user.employee.id, date=today).first()

    now_time = datetime.now().time()
    if not record:
        record = Attendance(
            employee_id=user.employee.id,
            date=today,
            status="Present",
            check_in=now_time,
            is_late=now_time.hour >= 10
        )
        db.session.add(record)
    else:
        if record.check_in:
            return jsonify({"success": False, "error": "Already checked in today"}), 400
        record.check_in = now_time
        record.status = "Present"

    db.session.commit()
    return jsonify({
        "success": True,
        "message": "Checked in successfully",
        "check_in": now_time.strftime("%H:%M:%S")
    }), 200


@attendance_api_bp.route("/check-out", methods=["POST"])
@jwt_required
def api_check_out():
    """Mobile / Web clock-out for the authenticated employee."""
    user = request.current_jwt_user
    if not user.employee:
        return jsonify({"success": False, "error": "No employee profile found"}), 404

    today = date.today()
    record = Attendance.query.filter_by(employee_id=user.employee.id, date=today).first()
    if not record or not record.check_in:
        return jsonify({"success": False, "error": "You must check in first before checking out"}), 400

    now_time = datetime.now().time()
    record.check_out = now_time

    # Calculate hours worked
    t_in = datetime.combine(today, record.check_in)
    t_out = datetime.combine(today, now_time)
    diff_hrs = round((t_out - t_in).total_seconds() / 3600.0, 2)
    record.working_hours = max(diff_hrs, 0.0)
    record.overtime_hours = max(record.working_hours - 8.0, 0.0)

    db.session.commit()
    return jsonify({
        "success": True,
        "message": "Checked out successfully",
        "check_out": now_time.strftime("%H:%M:%S"),
        "working_hours": record.working_hours
    }), 200
