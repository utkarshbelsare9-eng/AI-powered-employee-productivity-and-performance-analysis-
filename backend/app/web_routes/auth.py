import secrets
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, request, flash, session, current_app
from flask_login import login_user, logout_user, login_required, current_user

from app.models import db
from app.models.user import User
from app.models.employee import Employee
from app.models.department import Department
from app.models.notification import Notification
from app.utils.mailer import send_password_reset_code

auth_bp = Blueprint("auth", __name__)

# In-memory reset tracker: user_id -> {"code": code, "expires_at": datetime}
ACTIVE_RESETS = {}


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()

        if user and user.check_password(password):
            if not user.is_active_account:
                if user.role in ("admin", "manager") and not user.last_login:
                    flash("Your Admin/Manager registration is pending approval by an administrator.", "warning")
                else:
                    flash("This account is currently disabled. Please contact an administrator.", "danger")
            else:
                login_user(user, remember=remember)
                user.last_login = datetime.utcnow()
                db.session.commit()
                session.permanent = True
                flash(f"Welcome back, {user.username}!", "success")
                next_page = request.args.get("next")
                return redirect(next_page or url_for("dashboard.index"))
        else:
            flash("Invalid username/email or password.", "danger")

    return render_template("login.html")


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    """Public registration entry point for ADMIN/MANAGER accounts only.

    New accounts are created inactive and must be approved by an existing
    administrator. Employee accounts cannot be created through this page.
    """
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    departments = Department.query.order_by(Department.name).all()

    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        email = request.form.get("email", "").strip().lower()
        name = request.form.get("name", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        role = request.form.get("role", "").strip().lower()
        department_id_raw = request.form.get("department_id", "").strip()

        errors = []
        if role not in ("admin", "manager"):
            errors.append("Only Admin or Manager registration is allowed.")
        if not username or len(username) < 3 or len(username) > 80:
            errors.append("Username must be between 3 and 80 characters.")
        if not email or "@" not in email or len(email) > 120:
            errors.append("Enter a valid email address.")
        if not name or len(name) < 2:
            errors.append("Full name is required.")
        if len(password) < 8:
            errors.append("Password must contain at least 8 characters.")
        if password != confirm_password:
            errors.append("Passwords do not match.")
        if User.query.filter_by(username=username).first():
            errors.append("Username is already registered.")
        if User.query.filter_by(email=email).first():
            errors.append("Email is already registered.")

        department_id = None
        if department_id_raw:
            try:
                department_id = int(department_id_raw)
                if not Department.query.get(department_id):
                    errors.append("Selected department is invalid.")
            except ValueError:
                errors.append("Selected department is invalid.")

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("signup.html", departments=departments)

        user = User(
            username=username,
            email=email,
            role=role,
            is_active_account=False,  # admin approval required
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        # Create the profile row so manager/admin accounts work consistently
        # with the rest of the application after approval.
        code = f"USR-{user.id:06d}"
        employee = Employee(
            employee_code=code,
            user_id=user.id,
            name=name,
            email=email,
            designation="System Administrator" if role == "admin" else "Manager",
            joining_date=datetime.utcnow().date(),
            status="Active",
            department_id=department_id,
        )
        db.session.add(employee)
        db.session.commit()

        flash(
            "Registration submitted successfully. Your Admin/Manager account is pending approval by an existing administrator.",
            "success",
        )
        return redirect(url_for("auth.login"))

    return render_template("signup.html", departments=departments)


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        identity = request.form.get("identity", "").strip()
        user = User.query.filter(
            (User.username == identity) | (User.email == identity)
        ).first()

        target_email = current_app.config.get("FORGOT_PASSWORD_TARGET_EMAIL", "utkarshbelsare9@gmail.com")

        if not user:
            flash(f"No account found with username or email '{identity}'.", "danger")
            return render_template("forgot_password.html")

        # Generate a secure 6-digit verification code
        code = f"{secrets.randbelow(900000) + 100000}"
        expires_at = datetime.utcnow() + timedelta(minutes=15)

        # Store in session and in ACTIVE_RESETS dictionary
        session["reset_user_id"] = user.id
        session["reset_code"] = code
        session["reset_expires_at"] = expires_at.isoformat()
        session["reset_target_email"] = target_email

        ACTIVE_RESETS[user.id] = {
            "code": code,
            "expires_at": expires_at,
            "username": user.username,
        }

        # Record in-app notification for all admin accounts
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
            print(f"[AUTH ERROR] Failed to record admin notification: {ex}")

        # Send email to utkarshbelsare9@gmail.com
        sent, detail = send_password_reset_code(user, code, target_email=target_email)

        if sent:
            flash("A 6-digit verification code has been sent directly to the Admin's email. Please obtain the code from the Admin to proceed.", "success")
        else:
            flash("A 6-digit verification code has been dispatched directly to the Admin's email. Please contact the Admin to obtain your code.", "info")

        return redirect(url_for("auth.reset_password"))

    return render_template("forgot_password.html")


@auth_bp.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    user_id = session.get("reset_user_id")
    target_email = session.get("reset_target_email", current_app.config.get("FORGOT_PASSWORD_TARGET_EMAIL", "utkarshbelsare9@gmail.com"))

    if not user_id:
        flash("Please request a password reset code first.", "warning")
        return redirect(url_for("auth.forgot_password"))

    user = User.query.get(user_id)
    if not user:
        session.pop("reset_user_id", None)
        flash("Invalid reset session. Please try again.", "danger")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        entered_code = request.form.get("code", "").strip()
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        # Validate stored code & expiration
        valid_code = session.get("reset_code")
        expires_str = session.get("reset_expires_at")

        # Fallback to ACTIVE_RESETS tracker
        if not valid_code and user.id in ACTIVE_RESETS:
            valid_code = ACTIVE_RESETS[user.id]["code"]
            expires_str = ACTIVE_RESETS[user.id]["expires_at"].isoformat()

        is_expired = True
        if expires_str:
            try:
                expires_dt = datetime.fromisoformat(expires_str)
                is_expired = datetime.utcnow() > expires_dt
            except Exception:
                is_expired = True

        if is_expired:
            flash("The verification code has expired. Please request a new one.", "danger")
            return render_template("reset_password.html", target_email=target_email)

        if not valid_code or entered_code != valid_code:
            flash("Incorrect verification code. Please check the code sent to Admin.", "danger")
            return render_template("reset_password.html", target_email=target_email)

        if len(new_password) < 6:
            flash("New password must be at least 6 characters long.", "warning")
            return render_template("reset_password.html", target_email=target_email)

        if new_password != confirm_password:
            flash("Passwords do not match. Please re-enter.", "warning")
            return render_template("reset_password.html", target_email=target_email)

        # Update password
        user.set_password(new_password)
        db.session.commit()

        # Clear reset session & tracker
        session.pop("reset_user_id", None)
        session.pop("reset_code", None)
        session.pop("reset_expires_at", None)
        session.pop("reset_target_email", None)
        ACTIVE_RESETS.pop(user.id, None)

        flash("Password reset successfully! You can now sign in with your new password.", "success")
        return redirect(url_for("auth.login"))

    return render_template("reset_password.html", target_email=target_email)


@auth_bp.route("/resend-code", methods=["POST"])
def resend_code():
    user_id = session.get("reset_user_id")
    if not user_id:
        flash("No active password reset request. Please submit your username or email.", "warning")
        return redirect(url_for("auth.forgot_password"))

    user = User.query.get(user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("auth.forgot_password"))

    target_email = current_app.config.get("FORGOT_PASSWORD_TARGET_EMAIL", "utkarshbelsare9@gmail.com")
    code = f"{secrets.randbelow(900000) + 100000}"
    expires_at = datetime.utcnow() + timedelta(minutes=15)

    session["reset_code"] = code
    session["reset_expires_at"] = expires_at.isoformat()
    session["reset_target_email"] = target_email

    ACTIVE_RESETS[user.id] = {
        "code": code,
        "expires_at": expires_at,
        "username": user.username,
    }

    sent, detail = send_password_reset_code(user, code, target_email=target_email)
    if sent:
        flash("A new verification code has been sent directly to the Admin's email.", "success")
    else:
        flash("A new verification code has been dispatched directly to the Admin's email. Please contact the Admin to obtain your code.", "info")

    return redirect(url_for("auth.reset_password"))


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("auth.login"))
