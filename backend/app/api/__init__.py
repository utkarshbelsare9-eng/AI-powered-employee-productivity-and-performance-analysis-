from flask import Blueprint
from app.api.routes.auth import auth_api_bp
from app.api.routes.employees import employees_api_bp
from app.api.routes.attendance import attendance_api_bp
from app.api.routes.tasks import tasks_api_bp
from app.api.routes.predictions import predictions_api_bp
from app.api.routes.analytics import analytics_api_bp
from app.api.routes.leaves import leaves_api_bp
from app.api.routes.activity import activity_api_bp

api_v1_bp = Blueprint("api_v1", __name__, url_prefix="/api/v1")

# Register child blueprints
api_v1_bp.register_blueprint(auth_api_bp)
api_v1_bp.register_blueprint(employees_api_bp)
api_v1_bp.register_blueprint(attendance_api_bp)
api_v1_bp.register_blueprint(tasks_api_bp)
api_v1_bp.register_blueprint(predictions_api_bp)
api_v1_bp.register_blueprint(analytics_api_bp)
api_v1_bp.register_blueprint(leaves_api_bp)
api_v1_bp.register_blueprint(activity_api_bp)
