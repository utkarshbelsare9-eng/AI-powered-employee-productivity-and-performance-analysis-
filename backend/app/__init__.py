import os
import sys

# Ensure backend package resolution
BACKEND_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from flask import Flask, render_template
from flask_login import current_user
from app.config import Config
from app.extensions import db, login_manager, csrf, cors


def create_app(config_class=Config):
    # Setup template and static folders pointing to frontend/web
    project_root = config_class.PROJECT_ROOT
    template_dir = os.path.join(project_root, "frontend", "web", "templates")
    static_dir = os.path.join(project_root, "frontend", "web", "static")

    # Fallback to local templates/static if ever missing
    if not os.path.exists(template_dir):
        template_dir = os.path.join(project_root, "templates")
    if not os.path.exists(static_dir):
        static_dir = os.path.join(project_root, "static")

    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

    # Register API v1 Blueprints
    from app.api import (
        api_v1_bp, auth_api_bp, employees_api_bp, attendance_api_bp,
        tasks_api_bp, predictions_api_bp, analytics_api_bp, leaves_api_bp, activity_api_bp
    )
    for bp in (
        api_v1_bp, auth_api_bp, employees_api_bp, attendance_api_bp,
        tasks_api_bp, predictions_api_bp, analytics_api_bp, leaves_api_bp, activity_api_bp
    ):
        csrf.exempt(bp)

    app.register_blueprint(api_v1_bp)

    # Register Web View Blueprints
    from app.web_routes.auth import auth_bp
    from app.web_routes.dashboard import dashboard_bp
    from app.web_routes.employees import employees_bp
    from app.web_routes.attendance import attendance_bp
    from app.web_routes.tasks import tasks_bp
    from app.web_routes.analytics import analytics_bp
    from app.web_routes.prediction import prediction_bp
    from app.web_routes.reports import reports_bp
    from app.web_routes.admin import admin_bp
    from app.web_routes.profile import profile_bp
    from app.web_routes.api import api_bp
    from app.web_routes.activity import activity_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(prediction_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(activity_bp)

    # Context processors
    @app.context_processor
    def inject_globals():
        from datetime import date
        from app.models.notification import Notification
        unread = 0
        if current_user.is_authenticated:
            unread = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        return {"app_name": "ProductivityAI", "today": date.today(), "unread_notifications": unread}

    # Error handlers
    @app.errorhandler(401)
    def unauthorized(e):
        return render_template("errors/401.html"), 401

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    return app
