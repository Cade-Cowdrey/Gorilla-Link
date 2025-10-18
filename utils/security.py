from functools import wraps
from flask import abort
from flask_login import current_user
from werkzeug.security import generate_password_hash, check_password_hash


def hash_password(plain: str) -> str:
    return generate_password_hash(plain)


def verify_password(pw_hash: str, candidate: str) -> bool:
    try:
        return check_password_hash(pw_hash, candidate)
    except Exception:
        return False


def roles_required(*roles):
    """Decorate views to allow only certain user roles (e.g., 'admin')."""
    def wrapper(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if getattr(current_user, "role", None) not in roles:
                abort(403)
            return fn(*args, **kwargs)
        return decorated
    return wrapper
