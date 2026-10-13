import functools
import jwt
from datetime import datetime, timezone
from flask import request, jsonify, current_app
from app.models.user import User


def jwt_required(f):
    """Decorator to require a valid Bearer JWT for mobile and API clients."""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({
                "success": False,
                "error": "Authorization header missing or invalid format (Bearer <token> required)"
            }), 401

        token = auth_header.split(" ", 1)[1].strip()
        try:
            payload = jwt.decode(
                token,
                current_app.config["JWT_SECRET_KEY"],
                algorithms=["HS256"]
            )
            user_id = payload.get("user_id")
            user = User.query.get(user_id)
            if not user or not user.is_active_account:
                return jsonify({"success": False, "error": "User inactive or not found"}), 401
            
            # Attach authenticated user to request context
            request.current_jwt_user = user
        except jwt.ExpiredSignatureError:
            return jsonify({"success": False, "error": "Token has expired"}), 401
        except jwt.InvalidTokenError as e:
            return jsonify({"success": False, "error": f"Invalid token: {str(e)}"}), 401

        return f(*args, **kwargs)
    return decorated_function


def api_role_required(*roles):
    """Ensure the authenticated JWT user has one of the specified roles."""
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            user = getattr(request, "current_jwt_user", None)
            if not user:
                return jsonify({"success": False, "error": "Authentication required"}), 401
            if user.role not in roles:
                return jsonify({
                    "success": False,
                    "error": f"Permission denied. Required role in {roles}, user is '{user.role}'"
                }), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def generate_jwt_token(user):
    """Generate a signed JWT token for mobile client authentication."""
    expiration = datetime.now(timezone.utc) + current_app.config["PERMANENT_SESSION_LIFETIME"]
    payload = {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "exp": expiration
    }
    return jwt.encode(payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256")
