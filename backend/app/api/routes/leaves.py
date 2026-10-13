from flask import Blueprint, request, jsonify
from datetime import datetime, date
from app.extensions import db
from app.models.leave import Leave
from app.models.employee import Employee
from app.api.auth_middleware import jwt_required, api_role_required

leaves_api_bp = Blueprint("api_leaves", __name__, url_prefix="/leaves")


@leaves_api_bp.route("", methods=["GET"])
@jwt_required
def get_leaves():
    """List leaves for self or team."""
    user = request.current_jwt_user
    query = Leave.query

    if user.role == "employee":
        if user.employee:
            query = query.filter_by(employee_id=user.employee.id)
    elif user.role == "manager" and user.employee:
        team_ids = [e.id for e in Employee.query.filter_by(manager_id=user.employee.id).all()]
        query = query.filter(Leave.employee_id.in_(team_ids)) if team_ids else query.filter(False)

    leaves = query.order_by(Leave.applied_on.desc()).all()

    return jsonify({
        "success": True,
        "count": len(leaves),
        "leaves": [{
            "id": l.id,
            "employee_id": l.employee_id,
            "employee_name": l.employee.name if l.employee else None,
            "leave_type": l.leave_type,
            "start_date": l.start_date.isoformat(),
            "end_date": l.end_date.isoformat(),
            "reason": l.reason,
            "status": l.status,
            "applied_on": l.applied_on.isoformat()
        } for l in leaves]
    }), 200


@leaves_api_bp.route("", methods=["POST"])
@jwt_required
def apply_leave():
    """Submit a leave application."""
    user = request.current_jwt_user
    if not user.employee:
        return jsonify({"success": False, "error": "No employee profile found"}), 404

    data = request.get_json(silent=True) or {}
    start_str = data.get("start_date")
    end_str = data.get("end_date")
    leave_type = data.get("leave_type", "Casual")
    reason = data.get("reason", "")

    if not start_str or not end_str:
        return jsonify({"success": False, "error": "start_date and end_date are required"}), 400

    try:
        start_d = datetime.strptime(start_str, "%Y-%m-%d").date()
        end_d = datetime.strptime(end_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"success": False, "error": "Invalid date format (use YYYY-MM-DD)"}), 400

    leave = Leave(
        employee_id=user.employee.id,
        leave_type=leave_type,
        start_date=start_d,
        end_date=end_d,
        reason=reason,
        status="Pending",
        applied_on=date.today()
    )
    db.session.add(leave)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Leave application submitted successfully",
        "leave_id": leave.id
    }), 201


@leaves_api_bp.route("/<int:leave_id>/decision", methods=["POST"])
@jwt_required
@api_role_required("admin", "manager")
def approve_or_reject_leave(leave_id):
    """Approve or reject a leave application."""
    leave = Leave.query.get(leave_id)
    if not leave:
        return jsonify({"success": False, "error": "Leave request not found"}), 404

    data = request.get_json(silent=True) or {}
    decision = data.get("decision")  # Approved or Rejected
    if decision not in ("Approved", "Rejected"):
        return jsonify({"success": False, "error": "Decision must be 'Approved' or 'Rejected'"}), 400

    leave.status = decision
    db.session.commit()

    return jsonify({
        "success": True,
        "message": f"Leave application {decision.lower()}",
        "leave_id": leave.id,
        "status": leave.status
    }), 200
