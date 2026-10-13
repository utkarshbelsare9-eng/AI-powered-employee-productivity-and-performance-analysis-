import os
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user

from app.models import db
from app.utils.helpers import allowed_file

profile_bp = Blueprint("profile", __name__)


@profile_bp.route("/profile")
@login_required
def my_profile():
    emp = current_user.employee
    timesheet_rows = []
    if emp:
        from app.web_routes.activity import build_timesheet_rows
        timesheet_rows = build_timesheet_rows(emp.id, num_days=7)
    return render_template("profile.html", emp=emp, is_own_profile=True, timesheet_rows=timesheet_rows)


@profile_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        action = request.form.get("action")

        if action == "change_password":
            current_pw = request.form.get("current_password")
            new_pw = request.form.get("new_password")
            confirm_pw = request.form.get("confirm_password")
            if not current_user.check_password(current_pw):
                flash("Current password is incorrect.", "danger")
            elif new_pw != confirm_pw:
                flash("New passwords do not match.", "danger")
            elif len(new_pw) < 6:
                flash("New password must be at least 6 characters.", "danger")
            else:
                current_user.set_password(new_pw)
                db.session.commit()
                flash("Password changed successfully.", "success")

        elif action == "update_preferences":
            current_user.theme = request.form.get("theme", "light")
            current_user.language = request.form.get("language", "en")
            db.session.commit()
            flash("Preferences updated.", "success")

        elif action == "update_picture":
            file = request.files.get("profile_picture")
            if file and allowed_file(file.filename, {"png", "jpg", "jpeg"}):
                filename = secure_filename(f"user_{current_user.id}_{file.filename}")
                path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
                os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
                file.save(path)
                current_user.profile_picture = filename
                db.session.commit()
                flash("Profile picture updated.", "success")
            else:
                flash("Please upload a valid image file (png/jpg).", "danger")

        return redirect(url_for("profile.settings"))

    return render_template("settings.html")
