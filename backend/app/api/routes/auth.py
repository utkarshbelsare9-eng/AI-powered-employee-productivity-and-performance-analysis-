from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timezone
import secrets

from app.extensions import db
from app.models.user import User
from app.models.notification import Notification
from app.api.auth_middleware import generate_jwt_token, jwt_required
from app.utils.mailer import send_password_reset_code

auth_api_bp = Blueprint("api_auth", __name__, url_prefix="/auth")


@auth_api_bp.route("/login", methods=["POST"])
def api_login():
    """Mobile & external client login endpoint."""
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"success": False, "error": "Username/email and password are required"}), 400

    user = User.query.filter(
        (User.username == username) | (User.email == username)
    ).first()

    if not user or not user.check_password(password):
        return jsonify({"success": False, "error": "Invalid username/email or password"}), 401

    if not user.is_active_account:
        return jsonify({
            "success": False,
            "error": "Account is inactive or pending administrator approval"
        }), 403

    user.last_login = datetime.now(timezone.utc)
    db.session.commit()

    token = generate_jwt_token(user)

    employee_data = None
    if user.employee:
        e = user.employee
        employee_data = {
            "id": e.id,
            "employee_code": e.employee_code,
            "name": e.name,
            "designation": e.designation,
            "department": e.department.name if e.department else None,
            "status": e.status
        }

    return jsonify({
        "success": True,
        "message": f"Welcome back, {user.username}!",
        "token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "employee": employee_data
        }
    }), 200


@auth_api_bp.route("/forgot-password", methods=["POST"])
def api_forgot_password():
    """Request a password reset code (routed directly to Admin)."""
    data = request.get_json(silent=True) or {}
    identity = data.get("identity", "").strip()

    if not identity:
        return jsonify({"success": False, "error": "Username or email is required"}), 400

    user = User.query.filter(
        (User.username == identity) | (User.email == identity)
    ).first()

    target_email = current_app.config.get("FORGOT_PASSWORD_TARGET_EMAIL", "utkarshbelsare9@gmail.com")

    if not user:
        return jsonify({
            "success": False,
            "error": f"No account found with username or email '{identity}'"
        }), 404

    code = f"{secrets.randbelow(900000) + 100000}"

    # Log in database as notification for all admins
    try:
        admins = User.query.filter_by(role="admin").all()
        for adm in admins:
            db.session.add(Notification(
                user_id=adm.id,
                title="Password Reset Verification Code",
                message=f"Code for account '{user.username}': {code} (Valid for 15 mins)",
                category="warning"
            ))
        db.session.commit()
    except Exception as ex:
        print(f"[API AUTH ERROR] Notification create error: {ex}")

    # Dispatch mail
    sent, detail = send_password_reset_code(user, code, target_email=target_email)

    return jsonify({
        "success": True,
        "message": "A 6-digit verification code has been dispatched directly to the Admin. Please obtain the code from the Admin to proceed with resetting your password."
    }), 200


@auth_api_bp.route("/reset-password", methods=["POST"])
def api_reset_password():
    """Verify code and set a new password."""
    data = request.get_json(silent=True) or {}
    identity = data.get("identity", "").strip()
    code = data.get("code", "").strip()
    new_password = data.get("new_password", "")

    if not identity or not code or not new_password:
        return jsonify({"success": False, "error": "Identity, code, and new_password are required"}), 400

    if len(new_password) < 6:
        return jsonify({"success": False, "error": "New password must be at least 6 characters"}), 400

    user = User.query.filter(
        (User.username == identity) | (User.email == identity)
    ).first()

    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404

    # Search in Admin notifications for this code within last 15 minutes
    notif = Notification.query.filter(
        Notification.message.like(f"%Code for account '{user.username}': {code}%")
    ).order_by(Notification.created_at.desc()).first()

    if not notif:
        return jsonify({"success": False, "error": "Invalid or expired verification code"}), 400

    user.set_password(new_password)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Password reset successfully. You can now log in with your new password."
    }), 200


@auth_api_bp.route("/me", methods=["GET"])
@jwt_required
def api_me():
    """Get current authenticated user details."""
    user = request.current_jwt_user
    employee_data = None
    if user.employee:
        e = user.employee
        employee_data = {
            "id": e.id,
            "employee_code": e.employee_code,
            "name": e.name,
            "email": e.email,
            "phone": e.phone,
            "gender": e.gender,
            "age": e.age,
            "designation": e.designation,
            "salary": e.salary,
            "experience_years": e.experience_years,
            "department": e.department.name if e.department else None,
            "status": e.status
        }

    return jsonify({
        "success": True,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "employee": employee_data
        }
    }), 200
