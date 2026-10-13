from flask import Blueprint, request, jsonify
from sqlalchemy import func
from app.extensions import db
from app.models.employee import Employee
from app.models.department import Department
from app.models.attendance import Attendance
from app.models.performance import Performance
from app.models.prediction import Prediction
from app.api.auth_middleware import jwt_required

analytics_api_bp = Blueprint("api_analytics", __name__, url_prefix="/analytics")


@analytics_api_bp.route("/dashboard", methods=["GET"])
@jwt_required
def get_dashboard_summary():
    """Retrieve company-wide analytics dashboard figures."""
    total_employees = Employee.query.filter_by(status="Active").count()
    total_depts = Department.query.count()

    # Grade distribution
    grades_query = db.session.query(
        Prediction.predicted_grade, func.count(Prediction.id)
    ).group_by(Prediction.predicted_grade).all()
    grade_dist = {g: count for g, count in grades_query if g}

    # Risk counts
    high_attrition = Prediction.query.filter(Prediction.attrition_risk_percent >= 65).count()
    high_burnout = Prediction.query.filter(Prediction.burnout_risk_percent >= 65).count()

    # Department average performance
    dept_scores = []
    departments = Department.query.all()
    for d in departments:
        emp_ids = [e.id for e in d.employees]
        if emp_ids:
            avg_score = db.session.query(func.avg(Performance.performance_score)).filter(
                Performance.employee_id.in_(emp_ids)
            ).scalar() or 0.0
        else:
            avg_score = 0.0
        dept_scores.append({
            "department": d.name,
            "average_score": round(avg_score, 1)
        })

    return jsonify({
        "success": True,
        "summary": {
            "total_active_employees": total_employees,
            "total_departments": total_depts,
            "high_attrition_risk_count": high_attrition,
            "high_burnout_risk_count": high_burnout
        },
        "grade_distribution": grade_dist,
        "department_scores": dept_scores
    }), 200
