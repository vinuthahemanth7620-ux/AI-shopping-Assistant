from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.utils.decorators import admin_required

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Public Landing Page Route"""
    return render_template('main/index.html')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Protected User Dashboard Route"""
    return render_template('main/dashboard.html')


@main_bp.route('/admin')
@admin_required
def admin_dashboard():
    """Protected Admin Dashboard Route (Admin Role Required)"""
    return render_template('main/dashboard.html')
