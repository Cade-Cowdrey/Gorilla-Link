# ---------------------------------------------
#  utils/security_util.py
# ---------------------------------------------
from functools import wraps
from flask import abort
from flask_login import current_user

def require_roles(*roles):
    """
    Usage:
      @require_roles('admin') or @require_roles('admin', 'staff')
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if roles and (current_user.role not in roles):
                abort(403)
            return fn(*args, **kwargs)
        return wrapper
    return decorator
