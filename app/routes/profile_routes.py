from flask import Blueprint

profile_bp = Blueprint('profile', __name__)


@profile_bp.route('/')
def user_profile():
    """User Profile Placeholder Route"""
    return "Profile Module Coming Soon"
