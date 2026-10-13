from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.employee import Employee
from app.models.prediction import Prediction
from app.models.performance import Performance
from app.api.auth_middleware import jwt_required, api_role_required
from app.machine_learning.predict import predict_employee

predictions_api_bp = Blueprint("api_predictions", __name__, url_prefix="/predictions")


@predictions_api_bp.route("/employee/<int:emp_id>", methods=["GET"])
@jwt_required
def get_prediction_for_employee(emp_id):
    """Run ML Random Forest prediction for a specific employee."""
    user = request.current_jwt_user
    if user.role == "employee" and user.employee and user.employee.id != emp_id:
        return jsonify({"success": False, "error": "Access denied"}), 403

    emp = Employee.query.get(emp_id)
    if not emp:
        return jsonify({"success": False, "error": "Employee not found"}), 404

    # Calculate real features from recent records
    perf = Performance.query.filter_by(employee_id=emp.id).order_by(Performance.month.desc()).first()
    
    attendance_pct = perf.attendance_percentage if perf else 85.0
    avg_hours = perf.avg_working_hours if perf else 8.0
    late_entries = perf.late_entries if perf else 1
    leave_days = perf.leave_days if perf else 2
    tasks_assigned = perf.tasks_assigned if perf else 10
    tasks_completed = perf.tasks_completed if perf else 9
    deadlines_missed = perf.deadlines_missed if perf else 0
    overtime_hours = perf.overtime_hours if perf else 4.0
    customer_rating = perf.customer_rating if perf else 4.0
    manager_rating = perf.manager_rating if perf else 4.2
    skill_score = sum(s.proficiency for s in emp.skills) / max(len(emp.skills), 1) * 20 if emp.skills else 75.0
    experience_years = emp.experience_years or 3.0

    feature_dict = {
        "attendance_percent": attendance_pct,
        "avg_working_hours": avg_hours,
        "late_entries": late_entries,
        "leave_days": leave_days,
        "tasks_assigned": tasks_assigned,
        "tasks_completed": tasks_completed,
        "deadlines_missed": deadlines_missed,
        "overtime_hours": overtime_hours,
        "customer_rating": customer_rating,
        "manager_rating": manager_rating,
        "skill_score": skill_score,
        "experience_years": experience_years,
    }

    try:
        import json
        result = predict_employee(feature_dict)
        
        # Save or update in database
        pred_record = Prediction.query.filter_by(employee_id=emp.id).first()
        if not pred_record:
            pred_record = Prediction(employee_id=emp.id)
            db.session.add(pred_record)

        pred_record.predicted_grade = result.get("predicted_grade")
        pred_record.confidence = result.get("confidence", 0.0)
        pred_record.probabilities = json.dumps(result.get("probabilities", {}))
        pred_record.risk_level = result.get("risk_level", "Low")
        pred_record.attrition_risk_percent = result.get("attrition_risk_percent", 0.0)
        pred_record.burnout_risk_percent = result.get("burnout_risk_percent", 0.0)
        pred_record.promotion_eligible = result.get("promotion_eligible", False)
        pred_record.recommendations = json.dumps(result.get("recommendations", []))
        db.session.commit()

        return jsonify({
            "success": True,
            "employee_id": emp.id,
            "employee_name": emp.name,
            "prediction": result
        }), 200

    except Exception as e:
        return jsonify({"success": False, "error": f"Prediction failed: {str(e)}"}), 500
