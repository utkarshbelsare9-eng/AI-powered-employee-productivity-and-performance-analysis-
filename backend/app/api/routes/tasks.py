from flask import Blueprint, request, jsonify
from datetime import datetime, date
from app.extensions import db
from app.models.task import Task
from app.models.employee import Employee
from app.api.auth_middleware import jwt_required, api_role_required

tasks_api_bp = Blueprint("api_tasks", __name__, url_prefix="/tasks")


@tasks_api_bp.route("", methods=["GET"])
@jwt_required
def get_tasks():
    """List tasks filtered by user role or employee id."""
    user = request.current_jwt_user
    status = request.args.get("status")
    emp_id = request.args.get("employee_id", type=int)

    query = Task.query
    if user.role == "employee":
        if user.employee:
            query = query.filter_by(employee_id=user.employee.id)
    elif emp_id:
        query = query.filter_by(employee_id=emp_id)

    if status:
        query = query.filter_by(status=status)

    tasks = query.order_by(Task.deadline.asc()).all()

    return jsonify({
        "success": True,
        "count": len(tasks),
        "tasks": [{
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "employee_id": t.employee_id,
            "employee_name": t.employee.name if t.employee else None,
            "priority": t.priority,
            "status": t.status,
            "deadline": t.deadline.isoformat() if t.deadline else None,
            "assigned_date": t.assigned_date.isoformat() if t.assigned_date else None,
            "completion_date": t.completion_date.isoformat() if t.completion_date else None
        } for t in tasks]
    }), 200


@tasks_api_bp.route("/<int:task_id>/status", methods=["PATCH"])
@jwt_required
def update_task_status(task_id):
    """Update task status (e.g. To Do, In Progress, Completed)."""
    user = request.current_jwt_user
    task = Task.query.get(task_id)
    if not task:
        return jsonify({"success": False, "error": "Task not found"}), 404

    # Permission check
    if user.role == "employee" and user.employee and task.employee_id != user.employee.id:
        return jsonify({"success": False, "error": "Access denied"}), 403

    data = request.get_json(silent=True) or {}
    new_status = data.get("status")
    if new_status not in ("To Do", "In Progress", "Completed", "Cancelled"):
        return jsonify({"success": False, "error": "Invalid status value"}), 400

    task.status = new_status
    if new_status == "Completed":
        task.completion_date = date.today()

    db.session.commit()
    return jsonify({
        "success": True,
        "message": f"Task updated to {new_status}",
        "task_id": task.id,
        "status": task.status
    }), 200


@tasks_api_bp.route("", methods=["POST"])
@jwt_required
@api_role_required("admin", "manager")
def create_task():
    """Create a new task (Manager / Admin only)."""
    data = request.get_json(silent=True) or {}
    title = data.get("title", "").strip()
    employee_id = data.get("employee_id")
    deadline_str = data.get("deadline")

    if not title or not employee_id:
        return jsonify({"success": False, "error": "Title and employee_id are required"}), 400

    emp = Employee.query.get(employee_id)
    if not emp:
        return jsonify({"success": False, "error": "Assigned employee not found"}), 404

    deadline = None
    if deadline_str:
        try:
            deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"success": False, "error": "Invalid deadline format (use YYYY-MM-DD)"}), 400

    task = Task(
        title=title,
        description=data.get("description", ""),
        employee_id=employee_id,
        priority=data.get("priority", "Medium"),
        status=data.get("status", "To Do"),
        deadline=deadline,
        assigned_date=date.today()
    )
    db.session.add(task)
    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Task created successfully",
        "task_id": task.id
    }), 201
