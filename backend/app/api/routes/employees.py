from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.employee import Employee
from app.models.department import Department
from app.api.auth_middleware import jwt_required, api_role_required

employees_api_bp = Blueprint("api_employees", __name__, url_prefix="/employees")


@employees_api_bp.route("", methods=["GET"])
@jwt_required
def get_employees():
    """List employees with optional department filter and pagination."""
    dept_id = request.args.get("department_id", type=int)
    search = request.args.get("search", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    query = Employee.query
    if dept_id:
        query = query.filter_by(department_id=dept_id)
    if search:
        query = query.filter(
            (Employee.name.ilike(f"%{search}%")) |
            (Employee.employee_code.ilike(f"%{search}%")) |
            (Employee.designation.ilike(f"%{search}%"))
        )

    pagination = query.order_by(Employee.id.asc()).paginate(page=page, per_page=per_page, error_out=False)
    
    items = []
    for e in pagination.items:
        items.append({
            "id": e.id,
            "employee_code": e.employee_code,
            "name": e.name,
            "email": e.email,
            "phone": e.phone,
            "designation": e.designation,
            "department": e.department.name if e.department else None,
            "department_id": e.department_id,
            "manager_id": e.manager_id,
            "status": e.status,
            "experience_years": e.experience_years
        })

    return jsonify({
        "success": True,
        "total": pagination.total,
        "page": page,
        "pages": pagination.pages,
        "employees": items
    }), 200


@employees_api_bp.route("/<int:emp_id>", methods=["GET"])
@jwt_required
def get_employee_detail(emp_id):
    """Retrieve full detail for a single employee."""
    emp = Employee.query.get(emp_id)
    if not emp:
        return jsonify({"success": False, "error": "Employee not found"}), 404

    # Restrict employee role from viewing others if not self
    current_u = request.current_jwt_user
    if current_u.role == "employee" and current_u.employee and current_u.employee.id != emp_id:
        return jsonify({"success": False, "error": "Access denied"}), 403

    return jsonify({
        "success": True,
        "employee": {
            "id": emp.id,
            "employee_code": emp.employee_code,
            "name": emp.name,
            "email": emp.email,
            "phone": emp.phone,
            "gender": emp.gender,
            "age": emp.age,
            "designation": emp.designation,
            "salary": emp.salary,
            "joining_date": emp.joining_date.isoformat() if emp.joining_date else None,
            "experience_years": emp.experience_years,
            "education": emp.education,
            "address": emp.address,
            "status": emp.status,
            "department": emp.department.name if emp.department else None,
            "skills": [{"name": s.skill_name, "proficiency": s.proficiency} for s in emp.skills]
        }
    }), 200


@employees_api_bp.route("/departments", methods=["GET"])
@jwt_required
def get_departments():
    """List all corporate departments."""
    depts = Department.query.order_by(Department.name.asc()).all()
    return jsonify({
        "success": True,
        "departments": [{
            "id": d.id,
            "name": d.name,
            "description": d.description,
            "employee_count": len(d.employees)
        } for d in depts]
    }), 200
