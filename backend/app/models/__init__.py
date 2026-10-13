from app.extensions import db, login_manager

# Import all models so they register with SQLAlchemy's metadata
from app.models.user import User          # noqa: E402,F401
from app.models.department import Department  # noqa: E402,F401
from app.models.employee import Employee   # noqa: E402,F401
from app.models.attendance import Attendance  # noqa: E402,F401
from app.models.activity import ActivityLog   # noqa: E402,F401
from app.models.task import Task           # noqa: E402,F401
from app.models.performance import Performance  # noqa: E402,F401
from app.models.prediction import Prediction    # noqa: E402,F401
from app.models.leave import Leave         # noqa: E402,F401
from app.models.skill import Skill         # noqa: E402,F401
from app.models.achievement import Achievement  # noqa: E402,F401
from app.models.notification import Notification  # noqa: E402,F401


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Desktop activity-agent authentication model
from app.models.activity_token import ActivityAgentToken
