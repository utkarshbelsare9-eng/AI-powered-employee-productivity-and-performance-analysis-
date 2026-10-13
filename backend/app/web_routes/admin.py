from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.models import db
from app.models.user import User
from app.models.employee import Employee
from app.models.leave import Leave
from app.models.notification import Notification
from app.utils.helpers import role_required

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin")
@login_required
@role_required("admin")
def admin_home():
    users = User.query.order_by(User.role, User.username).all()
    total_users = len(users)
    return render_template("admin.html", users=users, total_users=total_users)


@admin_bp.route("/admin/users/<int:user_id>/toggle", methods=["POST"])
@login_required
@role_required("admin")
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active_account = not user.is_active_account
    db.session.commit()
    flash(f"Account for {user.username} {'activated' if user.is_active_account else 'deactivated'}.", "info")
    return redirect(url_for("admin.admin_home"))


@admin_bp.route("/admin/users/<int:user_id>/approve", methods=["POST"])
@login_required
@role_required("admin")
def approve_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role not in ("admin", "manager"):
        flash("Only Admin/Manager registrations can be approved from this workflow.", "warning")
        return redirect(url_for("admin.admin_home"))

    user.is_active_account = True
    db.session.commit()
    flash(f"{user.role.title()} account for {user.username} approved successfully.", "success")
    return redirect(url_for("admin.admin_home"))


@admin_bp.route("/leaves")
@login_required
@role_required("admin", "manager")
def list_leaves():
    query = Leave.query
    if current_user.is_manager and current_user.employee:
        team_ids = [e.id for e in Employee.query.filter_by(manager_id=current_user.employee.id).all()]
        query = query.filter(Leave.employee_id.in_(team_ids)) if team_ids else query.filter(False)
    leaves = query.order_by(Leave.applied_on.desc()).all()
    return render_template("leaves.html", leaves=leaves)


@admin_bp.route("/leaves/<int:leave_id>/<action>", methods=["POST"])
@login_required
@role_required("admin", "manager")
def review_leave(leave_id, action):
    leave = Leave.query.get_or_404(leave_id)
    if action == "approve":
        leave.status = "Approved"
    elif action == "reject":
        leave.status = "Rejected"
    db.session.commit()
    flash(f"Leave request {leave.status.lower()}.", "success")
    return redirect(url_for("admin.list_leaves"))


@admin_bp.route("/notifications")
@login_required
def list_notifications():
    notes = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    for n in notes:
        n.is_read = True
    db.session.commit()
    return render_template("notifications.html", notifications=notes)
