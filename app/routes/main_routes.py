from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Landing Page Route (Foundation Skeleton)"""
    return render_template('main/index.html')


@main_bp.route('/dashboard')
def dashboard():
    """User Dashboard Route (Foundation Skeleton)"""
    return render_template('main/index.html')
