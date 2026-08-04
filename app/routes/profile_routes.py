from flask import Blueprint, render_template

profile_bp = Blueprint('profile', __name__)


@profile_bp.route('/')
def user_profile():
    """User Profile Route (Foundation Skeleton)"""
    return render_template('main/index.html')
