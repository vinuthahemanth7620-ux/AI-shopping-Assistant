from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user, login_required
from app.models.user import UserRole


def admin_required(f):
    """
    Decorator for routes that require Admin privileges.
    - If user is unauthenticated, redirects to login page.
    - If user is authenticated but not an Admin, flashes access denied and redirects to user dashboard.
    """
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        role_val = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
        if role_val != 'admin' and current_user.role != UserRole.ADMIN:
            flash('You do not have permission to access the Admin Dashboard.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

