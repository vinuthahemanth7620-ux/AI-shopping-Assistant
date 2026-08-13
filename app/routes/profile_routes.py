from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.login_history import LoginHistory

profile_bp = Blueprint('profile', __name__)


@profile_bp.route('/', methods=['GET', 'POST'])
@login_required
def user_profile():
    """
    Protected User Profile Route.
    Displays user account info, role status, recent login history, and profile updates.
    """
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        current_user.first_name = first_name
        current_user.last_name = last_name

        if new_password:
            if len(new_password) < 6:
                flash('Password must be at least 6 characters long.', 'danger')
                return redirect(url_for('profile.user_profile'))
            if new_password != confirm_password:
                flash('Passwords do not match. Please re-enter.', 'danger')
                return redirect(url_for('profile.user_profile'))
            current_user.set_password(new_password)

        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        except Exception:
            db.session.rollback()
            flash('Failed to update profile.', 'danger')

        return redirect(url_for('profile.user_profile'))

    recent_logins = LoginHistory.query.filter_by(user_id=current_user.id).order_by(LoginHistory.login_time.desc()).limit(5).all()

    return render_template(
        'profile.html',
        user=current_user,
        recent_logins=recent_logins
    )
